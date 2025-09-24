import os
import ssl
import json
import random
import time
import sys
import signal
import tempfile
import pathlib
import threading
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
import paho.mqtt.client as mqtt
import boto3
from botocore.exceptions import ClientError

# ── OpenAPI spec --------------------------------------------------------
OPENAPI_SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "VOLTTRON VEN Agent", "version": "1.0.0"},
    "paths": {
        "/health": {
            "get": {
                "summary": "Health check",
                "responses": {"200": {"description": "Service healthy"}}
            }
        }
    },
}

SWAGGER_HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>API Docs</title>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@4/swagger-ui.css">
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@4/swagger-ui-bundle.js"></script>
  <script>
    window.onload = () => { SwaggerUIBundle({ url: '/openapi.json', dom_id: '#swagger-ui' }); };
  </script>
</body>
</html>
"""

# ── helpers ────────────────────────────────────────────────────────────
def fetch_tls_creds_from_secrets(secret_name: str, region_name="us-west-2") -> dict | None:
    """Fetch TLS PEM contents from AWS Secrets Manager and write them to temp files."""
    try:
        client = boto3.client("secretsmanager", region_name=region_name)
        response = client.get_secret_value(SecretId=secret_name)
        secret = json.loads(response["SecretString"])
        cert_files = {}
        tmp_dir = pathlib.Path(tempfile.gettempdir())

        for key, filename in {
            "ca_cert": "ca_cert.pem",
            "client_cert": "client_cert.pem",
            "private_key": "private_key.pem"
        }.items():
            if key in secret:
                path = tmp_dir / filename
                path.write_text(secret[key])
                cert_files[key] = str(path)
        print("✅ Fetched TLS secrets from AWS Secrets Manager")
        return cert_files
    except ClientError as e:
        print(f"❌ Error fetching TLS secrets: {e}", file=sys.stderr)
        return None

def _materialise_pem(*var_names: str) -> str | None:
    """Return a file-path ready for paho.tls_set()."""
    for var_name in var_names:
        val = os.getenv(var_name)
        if not val:
            continue
        if val.startswith("-----BEGIN"):
            pem_path = pathlib.Path(tempfile.gettempdir()) / f"{var_name.lower()}.pem"
            pem_path.write_text(val)
            os.environ[var_name] = str(pem_path)
            return str(pem_path)
        return val
    return None


def _dnsname_matches(pattern: str, hostname: str) -> bool:
    pattern = pattern.lower()
    hostname = hostname.lower()

    if pattern.startswith("*."):
        suffix = pattern[1:]
        if not suffix or not hostname.endswith(suffix):
            return False
        prefix = hostname[: -len(suffix)]
        return bool(prefix) and "." not in prefix

    return pattern == hostname


def _ensure_expected_server_hostname(mqtt_client: mqtt.Client, expected: str) -> None:
    """Perform hostname verification manually when connect and TLS hosts differ."""
    hostname = expected.strip()
    if not hostname:
        raise ssl.SSLError("Expected TLS server hostname not provided")

    sock = mqtt_client.socket()
    if sock is None:
        raise ssl.SSLError("TLS socket not available for hostname verification")

    cert = sock.getpeercert()
    if not cert:
        raise ssl.SSLError("TLS peer certificate missing")

    dns_names = [value for key, value in cert.get("subjectAltName", ()) if key == "DNS"]
    if not dns_names:
        for subject in cert.get("subject", ()):  # fall back to CN when SAN absent
            for key, value in subject:
                if key.lower() == "commonname":
                    dns_names.append(value)

    if not dns_names:
        raise ssl.CertificateError("TLS certificate does not present any DNS names")

    for pattern in dns_names:
        if _dnsname_matches(pattern, hostname):
            return

    raise ssl.CertificateError(
        f"Hostname '{hostname}' does not match certificate names: {dns_names}"
    )

# ── env / config ───────────────────────────────────────────────────────
MQTT_TOPIC_STATUS     = os.getenv("MQTT_TOPIC_STATUS", "volttron/dev")
MQTT_TOPIC_EVENTS     = os.getenv("MQTT_TOPIC_EVENTS", "openadr/event")
MQTT_TOPIC_RESPONSES  = os.getenv("MQTT_TOPIC_RESPONSES", "openadr/response")
MQTT_TOPIC_METERING   = os.getenv("MQTT_TOPIC_METERING", "volttron/metering")
DEFAULT_IOT_ENDPOINT  = "a1mgxpe8mg484j-ats.iot.us-west-2.amazonaws.com"
IOT_ENDPOINT          = os.getenv("IOT_ENDPOINT", DEFAULT_IOT_ENDPOINT)
MQTT_CONNECT_HOST     = os.getenv("IOT_CONNECT_HOST") or os.getenv("MQTT_CONNECT_HOST") or IOT_ENDPOINT
TLS_SERVER_HOSTNAME   = os.getenv("IOT_TLS_SERVER_NAME") or os.getenv("MQTT_TLS_SERVER_NAME") or IOT_ENDPOINT
try:
    MQTT_MAX_CONNECT_ATTEMPTS = int(os.getenv("MQTT_MAX_CONNECT_ATTEMPTS", "5"))
except ValueError:
    MQTT_MAX_CONNECT_ATTEMPTS = 5
MQTT_MAX_CONNECT_ATTEMPTS = max(1, MQTT_MAX_CONNECT_ATTEMPTS)
HEALTH_PORT           = int(os.getenv("HEALTH_PORT", "8000"))
TLS_SECRET_NAME       = os.getenv("TLS_SECRET_NAME","ven-mqtt-certs")
AWS_REGION            = os.getenv("AWS_REGION", "us-west-2")
MQTT_PORT             = int(os.getenv("MQTT_PORT", "8883"))
IOT_THING_NAME        = os.getenv("IOT_THING_NAME") or os.getenv("AWS_IOT_THING_NAME")
try:
    REPORT_INTERVAL_SECONDS = int(os.getenv("VEN_REPORT_INTERVAL_SECONDS", "10"))
except ValueError:
    REPORT_INTERVAL_SECONDS = 10
REPORT_INTERVAL_SECONDS = max(1, REPORT_INTERVAL_SECONDS)

if IOT_THING_NAME:
    SHADOW_TOPIC_UPDATE = f"$aws/things/{IOT_THING_NAME}/shadow/update"
    SHADOW_TOPIC_DELTA = f"{SHADOW_TOPIC_UPDATE}/delta"
    SHADOW_TOPIC_GET = f"$aws/things/{IOT_THING_NAME}/shadow/get"
    SHADOW_TOPIC_GET_ACCEPTED = f"{SHADOW_TOPIC_GET}/accepted"
    SHADOW_TOPIC_GET_REJECTED = f"{SHADOW_TOPIC_GET}/rejected"
else:
    SHADOW_TOPIC_UPDATE = None
    SHADOW_TOPIC_DELTA = None
    SHADOW_TOPIC_GET = None
    SHADOW_TOPIC_GET_ACCEPTED = None
    SHADOW_TOPIC_GET_REJECTED = None

# ── TLS setup ──────────────────────────────────────────────────────────
CA_CERT = CLIENT_CERT = PRIVATE_KEY = None

if TLS_SECRET_NAME:
    creds = fetch_tls_creds_from_secrets(TLS_SECRET_NAME, AWS_REGION)
    if creds:
        CA_CERT     = creds.get("ca_cert")
        CLIENT_CERT = creds.get("client_cert")
        PRIVATE_KEY = creds.get("private_key")

if not all([CA_CERT, CLIENT_CERT, PRIVATE_KEY]):
    CA_CERT     = _materialise_pem("CA_CERT", "CA_CERT_PEM")
    CLIENT_CERT = _materialise_pem("CLIENT_CERT", "CLIENT_CERT_PEM")
    PRIVATE_KEY = _materialise_pem("PRIVATE_KEY", "PRIVATE_KEY_PEM")

if not all([CA_CERT, CLIENT_CERT, PRIVATE_KEY]):
    print(
        "❌ TLS credentials are required for AWS IoT Core but were not provided",
        file=sys.stderr,
    )
    sys.exit(1)

# ── MQTT setup ─────────────────────────────────────────────────────────
client = mqtt.Client(protocol=mqtt.MQTTv311)
client.tls_set(
    ca_certs=CA_CERT,
    certfile=CLIENT_CERT,
    keyfile=PRIVATE_KEY,
    tls_version=ssl.PROTOCOL_TLSv1_2,
)
client.reconnect_delay_set(min_delay=1, max_delay=60)
manual_hostname_override = TLS_SERVER_HOSTNAME != MQTT_CONNECT_HOST
if manual_hostname_override:
    print(
        "🔐 TLS hostname override enabled: "
        f"connecting to {MQTT_CONNECT_HOST} but verifying certificate for {TLS_SERVER_HOSTNAME}"
    )
elif ".vpce." in MQTT_CONNECT_HOST:
    print(
        "⚠️ Connecting to an AWS IoT VPC endpoint without a TLS hostname override. "
        "Set IOT_TLS_SERVER_NAME to your IoT data endpoint to enable certificate checks.",
        file=sys.stderr,
    )
client.tls_insecure_set(manual_hostname_override)

connected = False
_reconnect_lock = threading.Lock()
_reconnect_in_progress = False
_shadow_state_lock = threading.Lock()
_shadow_reported_state: dict[str, Any] = {
    "status": {"ven": "starting", "mqtt_connected": False},
    "report_interval_seconds": REPORT_INTERVAL_SECONDS,
    "shadow_errors": {}
}
_shadow_target_power_kw: float | None = None


def _merge_dict(target: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _merge_dict(target[key], value)
        else:
            target[key] = value
    return target


def _shadow_merge_report(updates: dict[str, Any]) -> None:
    if not SHADOW_TOPIC_UPDATE or not updates:
        return

    with _shadow_state_lock:
        _merge_dict(_shadow_reported_state, updates)
        snapshot = deepcopy(_shadow_reported_state)

    payload = json.dumps({"state": {"reported": snapshot}})
    client.publish(SHADOW_TOPIC_UPDATE, payload, qos=1)
    print(f"Published thing shadow update: {payload}")


def _manual_hostname_verification(mqtt_client: mqtt.Client) -> None:
    if not manual_hostname_override:
        return
    try:
        _ensure_expected_server_hostname(mqtt_client, TLS_SERVER_HOSTNAME)
    except ssl.CertificateError as err:
        raise ssl.SSLError(str(err)) from err


def _on_connect(_client, _userdata, _flags, rc, *_args):
    global connected
    if rc == 0:
        try:
            _manual_hostname_verification(_client)
        except ssl.SSLError as err:
            connected = False
            print(f"MQTT connection failed TLS hostname check: {err}", file=sys.stderr)
            _client.disconnect()
            _shadow_merge_report({
                "status": {"mqtt_connected": False},
                "shadow_errors": {"tls_hostname": str(err)}
            })
            return
        connected = True
        _shadow_merge_report({"status": {"mqtt_connected": True}})
    else:
        connected = False
        _shadow_merge_report({
            "status": {"mqtt_connected": False, "last_connect_code": rc}
        })

    status = "established" if connected else f"failed (code {rc})"
    print(f"MQTT connection {status}")


def _on_disconnect(_client, _userdata, rc):
    global connected, _reconnect_in_progress
    connected = False
    reason = "graceful" if rc == mqtt.MQTT_ERR_SUCCESS else f"unexpected (code {rc})"
    print(f"MQTT disconnected: {reason}", file=sys.stderr)
    _shadow_merge_report({
        "status": {"mqtt_connected": False, "last_disconnect_code": rc}
    })

    if rc == mqtt.MQTT_ERR_SUCCESS:
        return

    def _attempt_reconnect():
        global _reconnect_in_progress
        with _reconnect_lock:
            if _reconnect_in_progress:
                return
            _reconnect_in_progress = True

        try:
            delay = 1
            for attempt in range(1, MQTT_MAX_CONNECT_ATTEMPTS + 1):
                try:
                    _client.reconnect()
                    return
                except Exception as err:  # pragma: no cover - informational
                    print(
                        f"MQTT reconnect failed (try {attempt}/{MQTT_MAX_CONNECT_ATTEMPTS}): {err}",
                        file=sys.stderr,
                    )
                    time.sleep(min(delay, 30))
                    delay *= 2
            print("❌ Could not reconnect to MQTT broker", file=sys.stderr)
        finally:
            with _reconnect_lock:
                _reconnect_in_progress = False

    threading.Thread(target=_attempt_reconnect, daemon=True).start()


def _shadow_request_sync() -> None:
    if not SHADOW_TOPIC_GET:
        return
    print(f"Requesting device shadow state for thing '{IOT_THING_NAME}'")
    client.publish(SHADOW_TOPIC_GET, json.dumps({}), qos=0)


def _sync_reported_state(reported: dict[str, Any]) -> None:
    global REPORT_INTERVAL_SECONDS, _shadow_target_power_kw
    if not isinstance(reported, dict):
        return

    if "report_interval_seconds" in reported:
        try:
            REPORT_INTERVAL_SECONDS = max(1, int(reported["report_interval_seconds"]))
        except (TypeError, ValueError):
            pass

    if "target_power_kw" in reported:
        try:
            _shadow_target_power_kw = float(reported["target_power_kw"])
        except (TypeError, ValueError):
            pass


def _apply_shadow_delta(delta: dict[str, Any]) -> dict[str, Any]:
    global REPORT_INTERVAL_SECONDS, _shadow_target_power_kw

    updates: dict[str, Any] = {}
    errors: dict[str, str] = {}

    for key, value in delta.items():
        if key == "report_interval_seconds":
            try:
                interval = max(1, int(value))
                REPORT_INTERVAL_SECONDS = interval
                updates[key] = interval
            except (TypeError, ValueError):
                errors[key] = f"invalid interval: {value}"
                updates[key] = REPORT_INTERVAL_SECONDS
        elif key == "target_power_kw":
            try:
                _shadow_target_power_kw = float(value)
                updates[key] = _shadow_target_power_kw
            except (TypeError, ValueError):
                errors[key] = f"invalid target_power_kw: {value}"
        else:
            updates[key] = value

    if errors:
        updates.setdefault("shadow_errors", {}).update(errors)

    status_updates = updates.setdefault("status", {})
    status_updates["last_shadow_delta_ts"] = int(time.time())
    status_updates["last_shadow_delta"] = deepcopy(delta)
    return updates


def on_shadow_delta(_client, _userdata, msg):
    if not SHADOW_TOPIC_DELTA:
        return

    try:
        payload = json.loads(msg.payload.decode())
    except json.JSONDecodeError as err:
        print(f"Invalid thing shadow delta payload: {err}", file=sys.stderr)
        _shadow_merge_report({"shadow_errors": {"delta_decode": str(err)}})
        return

    delta = payload.get("state") or {}
    if not isinstance(delta, dict):
        print(f"Unexpected thing shadow delta structure: {delta}", file=sys.stderr)
        _shadow_merge_report({"shadow_errors": {"delta_type": str(type(delta))}})
        return

    print(f"Received desired shadow state delta: {delta}")
    updates = _apply_shadow_delta(delta)
    if updates:
        _shadow_merge_report(updates)


def on_shadow_get_accepted(_client, _userdata, msg):
    if not SHADOW_TOPIC_GET_ACCEPTED:
        return

    try:
        payload = json.loads(msg.payload.decode())
    except json.JSONDecodeError as err:
        print(f"Invalid thing shadow document: {err}", file=sys.stderr)
        _shadow_merge_report({"shadow_errors": {"shadow_get": str(err)}})
        return

    state = payload.get("state") or {}
    desired = state.get("desired") or {}
    reported = state.get("reported") or {}
    print(f"Thing shadow get accepted: desired={desired}, reported={reported}")

    updates: dict[str, Any] = {"status": {"shadow_version": payload.get("version")}}

    if isinstance(desired, dict) and desired:
        desired_updates = _apply_shadow_delta(desired)
        _merge_dict(updates, desired_updates)
    elif isinstance(reported, dict) and reported:
        _sync_reported_state(reported)
        _merge_dict(updates, reported)

    _shadow_merge_report(updates)


def on_shadow_get_rejected(_client, _userdata, msg):
    if not SHADOW_TOPIC_GET_REJECTED:
        return

    try:
        error_payload = msg.payload.decode()
    except Exception:
        error_payload = repr(msg.payload)

    print(f"Thing shadow get rejected: {error_payload}", file=sys.stderr)
    _shadow_merge_report({"shadow_errors": {"shadow_get": error_payload}})


def _log_unhandled_message(_client, _userdata, msg):
    try:
        payload = msg.payload.decode()
    except Exception:
        payload = repr(msg.payload)
    print(f"Unhandled MQTT message on {msg.topic}: {payload}")

client.on_connect = _on_connect
client.on_disconnect = _on_disconnect
client.on_message = _log_unhandled_message

for attempt in range(1, MQTT_MAX_CONNECT_ATTEMPTS + 1):
    try:
        client.connect(MQTT_CONNECT_HOST, MQTT_PORT, 60)
        break
    except Exception as e:
        if client.is_connected():
            try:
                client.disconnect()
            except Exception:
                pass
        print(
            f"MQTT connect failed (try {attempt}/{MQTT_MAX_CONNECT_ATTEMPTS}): {e}",
            file=sys.stderr,
        )
        time.sleep(min(2 ** attempt, 30))
else:
    print("❌ Could not connect to MQTT broker", file=sys.stderr)
    sys.exit(1)

# ── graceful shutdown ─────────────────────────────────────────────────
def _shutdown(signo, _frame):
    print("Received SIGTERM, disconnecting cleanly…")
    client.loop_stop()
    client.disconnect()
    sys.exit(0)

signal.signal(signal.SIGTERM, _shutdown)

client.loop_start()

# ── simple /health endpoint -------------------------------------------
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/openapi.json":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(OPENAPI_SPEC).encode())
            return

        if self.path == "/docs":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(SWAGGER_HTML.encode())
            return

        status = 200 if connected else 503
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": connected}).encode())

def _start_health_server():
    HTTPServer(("0.0.0.0", HEALTH_PORT), HealthHandler).serve_forever()

threading.Thread(target=_start_health_server, daemon=True).start()
print(f"🩺 Health server running on port {HEALTH_PORT}")

# ── message handler ────────────────────────────────────────────────────
def _next_power_reading() -> float:
    with _shadow_state_lock:
        target = _shadow_target_power_kw

    if target is None:
        return round(random.uniform(0.5, 2.0), 2)

    jitter = random.uniform(-0.05, 0.05)
    return round(max(0.0, target + jitter), 2)


def on_event(_client, _userdata, msg):
    payload = json.loads(msg.payload.decode())
    print(f"Received event via MQTT: {payload}")
    response = {"ven_id": payload.get("ven_id", "ven123"), "response": "ack"}
    client.publish(MQTT_TOPIC_RESPONSES, json.dumps(response), qos=1)
    _shadow_merge_report({
        "status": {"last_event_ts": int(time.time())},
        "events": {"last": payload}
    })

# ── main loop ──────────────────────────────────────────────────────────
def main(iterations: int | None = None) -> None:
    client.message_callback_add(MQTT_TOPIC_EVENTS, on_event)
    client.subscribe(MQTT_TOPIC_EVENTS)

    if SHADOW_TOPIC_DELTA:
        client.message_callback_add(SHADOW_TOPIC_DELTA, on_shadow_delta)
        client.subscribe(SHADOW_TOPIC_DELTA)

        if SHADOW_TOPIC_GET_ACCEPTED:
            client.message_callback_add(SHADOW_TOPIC_GET_ACCEPTED, on_shadow_get_accepted)
            client.subscribe(SHADOW_TOPIC_GET_ACCEPTED)

        if SHADOW_TOPIC_GET_REJECTED:
            client.message_callback_add(SHADOW_TOPIC_GET_REJECTED, on_shadow_get_rejected)
            client.subscribe(SHADOW_TOPIC_GET_REJECTED)

        _shadow_request_sync()
    else:
        if not IOT_THING_NAME:
            print("⚠️ IOT_THING_NAME not set; device shadow sync disabled.")

    count = 0
    while True:
        now = int(time.time())
        status_payload = {"ven": "ready"}
        metering_payload = {
            "timestamp": now,
            "power_kw": _next_power_reading(),
        }

        client.publish(MQTT_TOPIC_STATUS, json.dumps(status_payload), qos=1)
        client.publish(MQTT_TOPIC_METERING, json.dumps(metering_payload), qos=1)
        print("Published VEN status and metering data to MQTT")

        with _shadow_state_lock:
            target_power_kw = _shadow_target_power_kw

        shadow_update = {
            "status": {
                "ven": "ready",
                "last_publish_ts": now,
                "mqtt_connected": connected
            },
            "metering": metering_payload,
            "report_interval_seconds": REPORT_INTERVAL_SECONDS,
        }

        if target_power_kw is not None:
            shadow_update["target_power_kw"] = target_power_kw

        _shadow_merge_report(shadow_update)

        count += 1
        if iterations is not None and count >= iterations:
            break
        time.sleep(REPORT_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
