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
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
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
        },
        "/config": {
            "get": {
                "summary": "Get current VEN configuration",
                "responses": {"200": {"description": "Current settings"}}
            },
            "post": {
                "summary": "Update VEN behaviour (interval/target)",
                "requestBody": {
                    "required": false,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "report_interval_seconds": {"type": "integer", "minimum": 1},
                                    "target_power_kw": {"type": "number"},
                                    "enabled": {"type": "boolean"},
                                    "meter_base_min_kw": {"type": "number", "minimum": 0},
                                    "meter_base_max_kw": {"type": "number", "minimum": 0},
                                    "meter_jitter_pct": {"type": "number", "minimum": 0, "maximum": 1},
                                    "voltage_enabled": {"type": "boolean"},
                                    "voltage_nominal": {"type": "number", "minimum": 1},
                                    "voltage_jitter_pct": {"type": "number", "minimum": 0, "maximum": 1},
                                    "current_enabled": {"type": "boolean"},
                                    "power_factor": {"type": "number", "minimum": 0.05, "maximum": 1}
                                }
                            }
                        }
                    }
                },
                "responses": {"200": {"description": "Applied and published"}}
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
  <div style="position:fixed;top:0;left:0;right:0;background:#0b5;color:#fff;padding:8px 12px;z-index:99;">
    <strong>VOLTTRON VEN</strong>
    <a href="/ui" style="color:#fff;margin-left:12px;text-decoration:underline;">Control UI</a>
    <a href="/config" style="color:#fff;margin-left:12px;text-decoration:underline;">Current Config (JSON)</a>
  </div>
  <div id="swagger-ui" style="margin-top:48px;"></div>
  <script src="https://unpkg.com/swagger-ui-dist@4/swagger-ui-bundle.js"></script>
  <script>
    window.onload = () => { SwaggerUIBundle({ url: '/openapi.json', dom_id: '#swagger-ui' }); };
  </script>
</body>
</html>
"""

CONFIG_UI_HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta charset=\"utf-8\"/>
  <title>VEN Control</title>
  <style>
    :root { --bg:#0b5; --card:#fff; --muted:#666; --accent:#0b5; }
    body { font-family: system-ui, sans-serif; margin: 0; line-height: 1.4; background:#f6f8fa; }
    header { background: var(--bg); color:#fff; padding:12px 16px; position:sticky; top:0; }
    header a { color:#fff; margin-left: 12px; text-decoration: underline; }
    main { max-width: 960px; margin: 24px auto; padding: 0 16px; }
    .grid { display:grid; grid-template-columns: repeat(auto-fit,minmax(280px,1fr)); gap:16px; }
    .card { background: var(--card); border-radius: 10px; padding:16px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
    .card h2 { margin:0 0 8px; font-size:1.1rem; }
    .field { display:flex; align-items:center; justify-content:space-between; gap:12px; margin:8px 0; }
    .field label { color: var(--muted); }
    .field input[type=\"number\"] { width: 140px; padding: 6px 8px; border:1px solid #ddd; border-radius:8px; }
    .field input[type=\"checkbox\"] { transform: scale(1.2); }
    .actions { display:flex; gap:12px; margin-top:12px; }
    button { background: var(--accent); color:#fff; border:0; border-radius:8px; padding:8px 14px; cursor:pointer; }
    button.secondary { background:#222; }
    .status { margin-top: 12px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; white-space:pre-wrap; }
  </style>
  <script>
    async function loadCurrent(){
      const r = await fetch('/config');
      if(!r.ok) return;
      const j = await r.json();
      document.getElementById('interval').value = j.report_interval_seconds ?? '';
      document.getElementById('target').value   = j.target_power_kw ?? '';
      document.getElementById('enabled').checked = !!j.enabled;
      // Metering knobs
      document.getElementById('base_min').value = j.meter_base_min_kw ?? 0.5;
      document.getElementById('base_max').value = j.meter_base_max_kw ?? 2.0;
      document.getElementById('jitter').value   = (j.meter_jitter_pct ?? 0.05);
      // Voltage
      document.getElementById('v_enabled').checked = !!j.voltage_enabled;
      document.getElementById('v_nom').value = j.voltage_nominal ?? 120.0;
      document.getElementById('v_jitter').value = (j.voltage_jitter_pct ?? 0.02);
      // Current
      document.getElementById('i_enabled').checked = !!j.current_enabled;
      document.getElementById('pf').value = j.power_factor ?? 1.0;
      document.getElementById('status').textContent = 'Current: ' + JSON.stringify(j, null, 2);
    }
    async function applyChanges(){
      const interval = document.getElementById('interval').value;
      const target   = document.getElementById('target').value;
      const enabled  = document.getElementById('enabled').checked;
      const body = {};
      if(interval) body.report_interval_seconds = Number(interval);
      if(target)   body.target_power_kw = Number(target);
      body.enabled = enabled;
      // Metering knobs
      body.meter_base_min_kw = Number(document.getElementById('base_min').value);
      body.meter_base_max_kw = Number(document.getElementById('base_max').value);
      body.meter_jitter_pct  = Number(document.getElementById('jitter').value);
      // Voltage knobs
      body.voltage_enabled   = document.getElementById('v_enabled').checked;
      body.voltage_nominal   = Number(document.getElementById('v_nom').value);
      body.voltage_jitter_pct= Number(document.getElementById('v_jitter').value);
      // Current knobs
      body.current_enabled   = document.getElementById('i_enabled').checked;
      body.power_factor      = Number(document.getElementById('pf').value);
      const r = await fetch('/config', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body)});
      const j = await r.json().catch(()=>({}));
      document.getElementById('status').textContent = 'Response: ' + JSON.stringify(j, null, 2);
    }
    window.addEventListener('DOMContentLoaded', loadCurrent);
  </script>
  </head>
  <body>
    <header>
      <strong>VOLTTRON VEN Control</strong>
      <a href="/docs">API Docs</a>
      <a href="/config">Current Config</a>
    </header>
    <main>
      <div class="grid">
        <section class="card">
          <h2>General</h2>
          <div class="field"><label>Enabled</label><input id="enabled" type="checkbox"/></div>
          <div class="field"><label>Report interval (s)</label><input id="interval" type="number" min="1" step="1" /></div>
          <div class="field"><label>Target power (kW)</label><input id="target" type="number" step="0.01" /></div>
        </section>

        <section class="card">
          <h2>Power Generation</h2>
          <div class="field"><label>Base min (kW)</label><input id="base_min" type="number" step="0.01" min="0" /></div>
          <div class="field"><label>Base max (kW)</label><input id="base_max" type="number" step="0.01" min="0" /></div>
          <div class="field"><label>Jitter (%) [0..1]</label><input id="jitter" type="number" step="0.005" min="0" max="1" /></div>
        </section>

        <section class="card">
          <h2>Voltage (optional)</h2>
          <div class="field"><label>Include voltage</label><input id="v_enabled" type="checkbox"/></div>
          <div class="field"><label>Nominal (V)</label><input id="v_nom" type="number" step="0.1" min="1" /></div>
          <div class="field"><label>Jitter (%) [0..1]</label><input id="v_jitter" type="number" step="0.005" min="0" max="1" /></div>
        </section>

        <section class="card">
          <h2>Current (optional)</h2>
          <div class="field"><label>Include current</label><input id="i_enabled" type="checkbox"/></div>
          <div class="field"><label>Power factor</label><input id="pf" type="number" step="0.01" min="0.05" max="1" /></div>
        </section>
      </div>
      <div class="actions">
        <button onclick="applyChanges()">Apply</button>
        <button class="secondary" onclick="loadCurrent()">Reload</button>
      </div>
      <div id="status" class="status"></div>
    </main>
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


def _format_timestamp(timestamp: float | None) -> str | None:
    if timestamp is None:
        return None

    return (
        datetime.fromtimestamp(timestamp, tz=timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


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
TLS_SECRET_NAME       = os.getenv("TLS_SECRET_NAME","dev-volttron-tls")
AWS_REGION            = os.getenv("AWS_REGION", "us-west-2")
MQTT_PORT             = int(os.getenv("MQTT_PORT", "8883"))
IOT_THING_NAME        = os.getenv("IOT_THING_NAME") or os.getenv("AWS_IOT_THING_NAME")
try:
    REPORT_INTERVAL_SECONDS = int(os.getenv("VEN_REPORT_INTERVAL_SECONDS", "60"))
except ValueError:
    REPORT_INTERVAL_SECONDS = 60
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
    
CLIENT_ID             = (
    os.getenv("IOT_CLIENT_ID")
    or os.getenv("CLIENT_ID")
    or os.getenv("AWS_IOT_THING_NAME")
    or os.getenv("THING_NAME")
    or "volttron_thing"
)

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

def _build_tls_context(
    ca_path: str, cert_path: str, key_path: str, expected_sni: str | None, connect_host: str
) -> ssl.SSLContext:
    """Create an SSLContext that always sends SNI=expected_sni when set.

    - Verifies the server certificate chain against the provided CA.
    - Keeps hostname verification enabled; when an SNI override is provided
      it causes Python to validate the certificate against that SNI value.
    - Ensures AWS IoT PrivateLink works by sending SNI for the public ATS host
      even when connecting to a VPCE DNS name.
    """
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=ca_path)
    ctx.load_cert_chain(certfile=cert_path, keyfile=key_path)

    # Enforce TLS 1.2+
    try:
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2  # type: ignore[attr-defined]
    except Exception:
        pass

    manual_override = bool(expected_sni) and expected_sni != connect_host
    if manual_override and hasattr(ctx, "wrap_socket"):
        # Monkey‑patch wrap_socket to force server_hostname to expected_sni
        orig_wrap = ctx.wrap_socket  # bound method

        def _wrap_socket_with_sni(sock, *args, **kwargs):  # type: ignore[override]
            kwargs["server_hostname"] = expected_sni
            return orig_wrap(sock, *args, **kwargs)

        ctx.wrap_socket = _wrap_socket_with_sni  # type: ignore[assignment]

    # Leave check_hostname=True so Python validates against server_hostname (SNI)
    ctx.check_hostname = True
    ctx.verify_mode = ssl.CERT_REQUIRED
    return ctx

# ── MQTT setup ─────────────────────────────────────────────────────────
client = mqtt.Client(client_id=CLIENT_ID, protocol=mqtt.MQTTv311)

manual_hostname_override = TLS_SERVER_HOSTNAME != MQTT_CONNECT_HOST
if manual_hostname_override:
    print(
        "🔐 TLS SNI override enabled: "
        f"connecting to {MQTT_CONNECT_HOST} but sending SNI/cert validation for {TLS_SERVER_HOSTNAME}"
    )
elif ".vpce." in MQTT_CONNECT_HOST:
    print(
        "⚠️ Connecting to an AWS IoT VPC endpoint without a TLS SNI override. "
        "Set IOT_TLS_SERVER_NAME to your IoT data endpoint to enable certificate checks.",
        file=sys.stderr,
    )

_tls_ctx = _build_tls_context(CA_CERT, CLIENT_CERT, PRIVATE_KEY, TLS_SERVER_HOSTNAME, MQTT_CONNECT_HOST)
client.tls_set_context(_tls_ctx)
client.reconnect_delay_set(min_delay=1, max_delay=60)

connected = False
_last_connect_time: float | None = None
_last_disconnect_time: float | None = None
_last_publish_time: float | None = None
_reconnect_lock = threading.Lock()
_reconnect_in_progress = False
_shadow_state_lock = threading.Lock()
_shadow_reported_state: dict[str, Any] = {
    "status": {"ven": "starting", "mqtt_connected": False},
    "report_interval_seconds": REPORT_INTERVAL_SECONDS,
    "shadow_errors": {}
}
_shadow_target_power_kw: float | None = None
_ven_enabled: bool = True

# ── Metering configuration knobs (tunable at runtime) -----------------------
_meter_base_min_kw: float = 0.5
_meter_base_max_kw: float = 2.0
_meter_jitter_pct: float = 0.05  # ±5% around target when set

_voltage_enabled: bool = False
_voltage_nominal: float = 120.0
_voltage_jitter_pct: float = 0.02  # ±2%

_current_enabled: bool = False
_power_factor: float = 1.0  # 0 < pf <= 1


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


def _shadow_publish_desired(desired: dict[str, Any]) -> None:
    if not SHADOW_TOPIC_UPDATE or not desired:
        return
    payload = json.dumps({"state": {"desired": desired}})
    client.publish(SHADOW_TOPIC_UPDATE, payload, qos=1)
    print(f"Published desired shadow update: {desired}")


def _manual_hostname_verification(mqtt_client: mqtt.Client) -> None:
    # With the SNI-forcing TLS context, Python already validated the
    # certificate against TLS_SERVER_HOSTNAME. Keep this as a belt‑and‑braces
    # check, but it should never fail unless the broker rotates certs mid‑session.
    if not manual_hostname_override:
        return
    try:
        _ensure_expected_server_hostname(mqtt_client, TLS_SERVER_HOSTNAME)
    except ssl.CertificateError as err:
        raise ssl.SSLError(str(err)) from err


def _on_connect(_client, _userdata, _flags, rc, *_args):
    global connected, _last_connect_time
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
        _last_connect_time = time.time()
        _shadow_merge_report({"status": {"mqtt_connected": True}})
    else:
        connected = False
        _shadow_merge_report({
            "status": {"mqtt_connected": False, "last_connect_code": rc}
        })

    status = "established" if connected else f"failed (code {rc})"
    print(f"MQTT connection {status} as client_id='{CLIENT_ID}'")


def _on_disconnect(_client, _userdata, rc):
    global connected, _reconnect_in_progress, _last_disconnect_time
    connected = False
    _last_disconnect_time = time.time()
    reason = "graceful" if rc == mqtt.MQTT_ERR_SUCCESS else f"unexpected (code {rc})"
    print(f"MQTT disconnected: {reason}", file=sys.stderr)
    _shadow_merge_report({
        "status": {"mqtt_connected": False, "last_disconnect_code": rc}
    })

    if rc == mqtt.MQTT_ERR_SUCCESS or not _ven_enabled:
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


def _subscribe_topics() -> None:
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


def _ven_disable() -> None:
    global _ven_enabled, connected
    _ven_enabled = False
    try:
        client.loop_stop()
    except Exception:
        pass
    try:
        client.disconnect()
    except Exception:
        pass
    connected = False


def _ven_enable() -> None:
    global _ven_enabled
    if _ven_enabled:
        return
    _ven_enabled = True
    # Try to connect and start loop, then resubscribe
    for attempt in range(1, MQTT_MAX_CONNECT_ATTEMPTS + 1):
        try:
            client.connect(MQTT_CONNECT_HOST, MQTT_PORT, 60)
            break
        except Exception as e:
            print(
                f"MQTT connect (re-enable) failed (try {attempt}/{MQTT_MAX_CONNECT_ATTEMPTS}): {e}",
                file=sys.stderr,
            )
            time.sleep(min(2 ** attempt, 30))
    client.loop_start()
    _subscribe_topics()


def _shadow_request_sync() -> None:
    if not SHADOW_TOPIC_GET:
        return
    print(f"Requesting device shadow state for thing '{IOT_THING_NAME}'")
    client.publish(SHADOW_TOPIC_GET, json.dumps({}), qos=0)


def _sync_reported_state(reported: dict[str, Any]) -> None:
    global REPORT_INTERVAL_SECONDS, _shadow_target_power_kw, _ven_enabled
    global _meter_base_min_kw, _meter_base_max_kw, _meter_jitter_pct
    global _voltage_enabled, _voltage_nominal, _voltage_jitter_pct
    global _current_enabled, _power_factor
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

    if "enabled" in reported:
        try:
            desired_enabled = bool(reported["enabled"])
            if desired_enabled and not _ven_enabled:
                _ven_enable()
            elif not desired_enabled and _ven_enabled:
                _ven_disable()
        except Exception:
            pass

    # Metering knobs
    try:
        if "meter_base_min_kw" in reported:
            _meter_base_min_kw = max(0.0, float(reported["meter_base_min_kw"]))
        if "meter_base_max_kw" in reported:
            _meter_base_max_kw = max(_meter_base_min_kw, float(reported["meter_base_max_kw"]))
        if "meter_jitter_pct" in reported:
            val = float(reported["meter_jitter_pct"])  # e.g., 0.05 = 5%
            _meter_jitter_pct = max(0.0, min(1.0, val))
    except (TypeError, ValueError):
        pass

    try:
        if "voltage_enabled" in reported:
            _voltage_enabled = bool(reported["voltage_enabled"])
        if "voltage_nominal" in reported:
            _voltage_nominal = max(1.0, float(reported["voltage_nominal"]))
        if "voltage_jitter_pct" in reported:
            val = float(reported["voltage_jitter_pct"])  # 0..1
            _voltage_jitter_pct = max(0.0, min(1.0, val))
    except (TypeError, ValueError):
        pass

    try:
        if "current_enabled" in reported:
            _current_enabled = bool(reported["current_enabled"])
        if "power_factor" in reported:
            val = float(reported["power_factor"])  # 0 < pf <= 1
            _power_factor = max(0.05, min(1.0, val))
    except (TypeError, ValueError):
        pass


def _apply_shadow_delta(delta: dict[str, Any]) -> dict[str, Any]:
    global REPORT_INTERVAL_SECONDS, _shadow_target_power_kw, _ven_enabled
    global _meter_base_min_kw, _meter_base_max_kw, _meter_jitter_pct
    global _voltage_enabled, _voltage_nominal, _voltage_jitter_pct
    global _current_enabled, _power_factor

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
        elif key == "enabled":
            try:
                desired_enabled = bool(value)
                if desired_enabled and not _ven_enabled:
                    _ven_enable()
                elif not desired_enabled and _ven_enabled:
                    _ven_disable()
                updates[key] = desired_enabled
            except Exception:
                errors[key] = f"invalid enabled: {value}"
        elif key == "meter_base_min_kw":
            try:
                _meter_base_min_kw = max(0.0, float(value))
                if _meter_base_max_kw < _meter_base_min_kw:
                    _meter_base_max_kw = _meter_base_min_kw
                updates[key] = _meter_base_min_kw
            except (TypeError, ValueError):
                errors[key] = f"invalid meter_base_min_kw: {value}"
        elif key == "meter_base_max_kw":
            try:
                _meter_base_max_kw = max(_meter_base_min_kw, float(value))
                updates[key] = _meter_base_max_kw
            except (TypeError, ValueError):
                errors[key] = f"invalid meter_base_max_kw: {value}"
        elif key == "meter_jitter_pct":
            try:
                val = float(value)
                _meter_jitter_pct = max(0.0, min(1.0, val))
                updates[key] = _meter_jitter_pct
            except (TypeError, ValueError):
                errors[key] = f"invalid meter_jitter_pct: {value}"
        elif key == "voltage_enabled":
            try:
                _voltage_enabled = bool(value)
                updates[key] = _voltage_enabled
            except Exception:
                errors[key] = f"invalid voltage_enabled: {value}"
        elif key == "voltage_nominal":
            try:
                _voltage_nominal = max(1.0, float(value))
                updates[key] = _voltage_nominal
            except (TypeError, ValueError):
                errors[key] = f"invalid voltage_nominal: {value}"
        elif key == "voltage_jitter_pct":
            try:
                val = float(value)
                _voltage_jitter_pct = max(0.0, min(1.0, val))
                updates[key] = _voltage_jitter_pct
            except (TypeError, ValueError):
                errors[key] = f"invalid voltage_jitter_pct: {value}"
        elif key == "current_enabled":
            try:
                _current_enabled = bool(value)
                updates[key] = _current_enabled
            except Exception:
                errors[key] = f"invalid current_enabled: {value}"
        elif key == "power_factor":
            try:
                val = float(value)
                _power_factor = max(0.05, min(1.0, val))
                updates[key] = _power_factor
            except (TypeError, ValueError):
                errors[key] = f"invalid power_factor: {value}"
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
def health_snapshot() -> tuple[int, dict]:
    """Return a status code and JSON payload describing service health."""
    payload = {
        "ok": connected,
        "status": "connected" if connected else "disconnected",
        "detail": (
            "MQTT connection established"
            if connected
            else "MQTT client disconnected; background reconnect active"
        ),
        "reconnect_in_progress": _reconnect_in_progress,
        "manual_tls_hostname_override": manual_hostname_override,
        "mqtt_connect_host": MQTT_CONNECT_HOST,
        "mqtt_port": MQTT_PORT,
        "tls_server_hostname": TLS_SERVER_HOSTNAME,
        "enabled": _ven_enabled,
    }

    if _last_connect_time is not None:
        payload["last_connected_at"] = _format_timestamp(_last_connect_time)
    if _last_disconnect_time is not None:
        payload["last_disconnect_at"] = _format_timestamp(_last_disconnect_time)
    if _last_publish_time is not None:
        payload["last_publish_at"] = _format_timestamp(_last_publish_time)

    return 200, payload


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/openapi.json":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(OPENAPI_SPEC).encode())
            return

        if path == "/docs":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(SWAGGER_HTML.encode())
            return

        if path in ("/", "/ui"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(CONFIG_UI_HTML.encode())
            return

        if path == "/config":
            with _shadow_state_lock:
                current = {
                    "report_interval_seconds": REPORT_INTERVAL_SECONDS,
                    "target_power_kw": _shadow_target_power_kw,
                    "enabled": _ven_enabled,
                    "meter_base_min_kw": _meter_base_min_kw,
                    "meter_base_max_kw": _meter_base_max_kw,
                    "meter_jitter_pct": _meter_jitter_pct,
                    "voltage_enabled": _voltage_enabled,
                    "voltage_nominal": _voltage_nominal,
                    "voltage_jitter_pct": _voltage_jitter_pct,
                    "current_enabled": _current_enabled,
                    "power_factor": _power_factor,
                }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(current).encode())
            return

        status, payload = health_snapshot()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())

    def do_POST(self):
        if self.path != "/config":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw.decode() or "{}")
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Invalid JSON")
            return

        # Accept only known keys
        desired: dict[str, Any] = {}
        if isinstance(body, dict):
            if "report_interval_seconds" in body:
                try:
                    desired["report_interval_seconds"] = max(1, int(body["report_interval_seconds"]))
                except (TypeError, ValueError):
                    pass
            if "target_power_kw" in body:
                try:
                    desired["target_power_kw"] = float(body["target_power_kw"])
                except (TypeError, ValueError):
                    pass
            if "enabled" in body:
                try:
                    desired["enabled"] = bool(body["enabled"])
                except Exception:
                    pass
            for fld in (
                "meter_base_min_kw",
                "meter_base_max_kw",
                "meter_jitter_pct",
                "voltage_enabled",
                "voltage_nominal",
                "voltage_jitter_pct",
                "current_enabled",
                "power_factor",
            ):
                if fld in body:
                    desired[fld] = body[fld]

        # Apply locally via the same code-path as IoT shadow deltas
        updates = _apply_shadow_delta(desired)
        if updates:
            _shadow_merge_report(updates)
        # And publish desired so remote shadow reflects the change
        _shadow_publish_desired(desired)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        with _shadow_state_lock:
            now_enabled = _ven_enabled
        resp = {"applied": desired, "current_interval": REPORT_INTERVAL_SECONDS, "enabled": now_enabled}
        self.wfile.write(json.dumps(resp).encode())

def _start_health_server():
    HTTPServer(("0.0.0.0", HEALTH_PORT), HealthHandler).serve_forever()

threading.Thread(target=_start_health_server, daemon=True).start()
print(f"🩺 Health server running on port {HEALTH_PORT}")

# ── message handler ────────────────────────────────────────────────────
def _next_power_reading() -> float:
    with _shadow_state_lock:
        target = _shadow_target_power_kw

    if target is None:
        # Base range when no target provided
        low, high = _meter_base_min_kw, _meter_base_max_kw
        if high < low:
            high = low
        return round(random.uniform(low, high), 2)

    # Jitter as a percentage of target (+/-)
    jitter = random.uniform(-_meter_jitter_pct, _meter_jitter_pct)
    return round(max(0.0, target * (1.0 + jitter)), 2)


def _next_voltage_reading() -> float:
    with _shadow_state_lock:
        nominal = _voltage_nominal
        jit = _voltage_jitter_pct
    jitter = random.uniform(-jit, jit)
    return round(max(1.0, nominal * (1.0 + jitter)), 1)


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
    global _last_publish_time
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
        # If VEN is disabled, do not publish or interact with MQTT.
        # Sleep briefly to keep CPU low, and allow /config UI to re-enable.
        if not _ven_enabled:
            time.sleep(1)
            continue

        now = int(time.time())
        status_payload = {"ven": "ready"}
        # Build metering payload with optional fields
        power_kw = _next_power_reading()
        metering_payload = {"timestamp": now, "power_kw": power_kw}
        with _shadow_state_lock:
            include_v = _voltage_enabled
            include_i = _current_enabled
            v_nom = _voltage_nominal
            pf = _power_factor

        if include_v:
            metering_payload["voltage_v"] = _next_voltage_reading()
            v_for_current = metering_payload["voltage_v"]
        else:
            v_for_current = v_nom

        if include_i and v_for_current > 0 and pf > 0:
            # P(kW) = V(V) * I(A) * PF / 1000  => I = P*1000/(V*PF)
            amps = (power_kw * 1000.0) / (v_for_current * pf)
            metering_payload["current_a"] = round(max(0.0, amps), 2)

        client.publish(MQTT_TOPIC_STATUS, json.dumps(status_payload), qos=1)
        client.publish(MQTT_TOPIC_METERING, json.dumps(metering_payload), qos=1)
        print("Published VEN status and metering data to MQTT")
        _last_publish_time = time.time()
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

        # Include current knob configuration in reported state for visibility.
        with _shadow_state_lock:
            shadow_update.update({
                "enabled": _ven_enabled,
                "meter_base_min_kw": _meter_base_min_kw,
                "meter_base_max_kw": _meter_base_max_kw,
                "meter_jitter_pct": _meter_jitter_pct,
                "voltage_enabled": _voltage_enabled,
                "voltage_nominal": _voltage_nominal,
                "voltage_jitter_pct": _voltage_jitter_pct,
                "current_enabled": _current_enabled,
                "power_factor": _power_factor,
            })

        _shadow_merge_report(shadow_update)

        count += 1
        if iterations is not None and count >= iterations:
            break
        time.sleep(REPORT_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
