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
from http.server import BaseHTTPRequestHandler, HTTPServer
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
DEFAULT_IOT_ENDPOINT  = "vpce-0d3cb8ea5764b8097-r1j8w787.data.iot.us-west-2.vpce.amazonaws.com"
IOT_ENDPOINT          = os.getenv("IOT_ENDPOINT", DEFAULT_IOT_ENDPOINT)
MQTT_CONNECT_HOST     = os.getenv("IOT_CONNECT_HOST") or os.getenv("MQTT_CONNECT_HOST") or IOT_ENDPOINT
TLS_SERVER_HOSTNAME   = os.getenv("IOT_TLS_SERVER_NAME") or os.getenv("MQTT_TLS_SERVER_NAME") or IOT_ENDPOINT
try:
    MQTT_MAX_CONNECT_ATTEMPTS = int(os.getenv("MQTT_MAX_CONNECT_ATTEMPTS", "5"))
except ValueError:
    MQTT_MAX_CONNECT_ATTEMPTS = 5
MQTT_MAX_CONNECT_ATTEMPTS = max(1, MQTT_MAX_CONNECT_ATTEMPTS)
HEALTH_PORT           = int(os.getenv("HEALTH_PORT", "8000"))
TLS_SECRET_NAME       = os.getenv("TLS_SECRET_NAME", "dev-volttron-tls")
AWS_REGION            = os.getenv("AWS_REGION", "us-west-2")
MQTT_PORT             = int(os.getenv("MQTT_PORT", "8883"))

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

def _on_connect(_client, _userdata, _flags, rc, *_args):
    global connected
    connected = rc == 0
    status = "established" if connected else f"failed (code {rc})"
    print(f"MQTT connection {status}")


def _on_disconnect(_client, _userdata, rc):
    global connected
    connected = False
    reason = "graceful" if rc == mqtt.MQTT_ERR_SUCCESS else f"unexpected (code {rc})"
    print(f"MQTT disconnected: {reason}", file=sys.stderr)

client.on_connect = _on_connect
client.on_disconnect = _on_disconnect

for attempt in range(1, MQTT_MAX_CONNECT_ATTEMPTS + 1):
    try:
        client.connect(MQTT_CONNECT_HOST, MQTT_PORT, 60)
        if manual_hostname_override:
            _ensure_expected_server_hostname(client, TLS_SERVER_HOSTNAME)
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
def on_event(_client, _userdata, msg):
    payload = json.loads(msg.payload.decode())
    print(f"Received event via MQTT: {payload}")
    response = {"ven_id": payload.get("ven_id", "ven123"), "response": "ack"}
    client.publish(MQTT_TOPIC_RESPONSES, json.dumps(response), qos=1)

# ── main loop ──────────────────────────────────────────────────────────
def main(iterations: int | None = None) -> None:
    client.subscribe(MQTT_TOPIC_EVENTS)
    client.on_message = on_event

    count = 0
    while True:
        client.publish(MQTT_TOPIC_STATUS,   json.dumps({"ven": "ready"}), qos=1)
        client.publish(MQTT_TOPIC_METERING, json.dumps({
            "timestamp": int(time.time()),
            "power_kw": round(random.uniform(0.5, 2.0), 2),
        }), qos=1)
        print("Published VEN status and metering data to MQTT")

        count += 1
        if iterations is not None and count >= iterations:
            break
        time.sleep(10)

if __name__ == "__main__":
    main()
