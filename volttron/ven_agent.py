# volttron/ven_agent.py
import os
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
def _materialise_pem(var_name: str) -> str | None:
    """Return a file-path ready for paho.tls_set()."""
    val = os.getenv(var_name)
    if not val:
        return None

    if val.startswith("-----BEGIN"):                     # looks like PEM
        pem_path = pathlib.Path(tempfile.gettempdir()) / f"{var_name.lower()}.pem"
        pem_path.write_text(val)
        os.environ[var_name] = str(pem_path)             # mutate for later debug
        return str(pem_path)

    return val                                           # already a path

# ── env / config ───────────────────────────────────────────────────────
MQTT_TOPIC_STATUS     = os.getenv("MQTT_TOPIC_STATUS", "volttron/dev")
MQTT_TOPIC_EVENTS     = os.getenv("MQTT_TOPIC_EVENTS", "openadr/event")
MQTT_TOPIC_RESPONSES  = os.getenv("MQTT_TOPIC_RESPONSES", "openadr/response")
MQTT_TOPIC_METERING   = os.getenv("MQTT_TOPIC_METERING", "volttron/metering")
IOT_ENDPOINT          = os.getenv("IOT_ENDPOINT", "localhost")

CA_CERT     = _materialise_pem("CA_CERT")
CLIENT_CERT = _materialise_pem("CLIENT_CERT")
PRIVATE_KEY = _materialise_pem("PRIVATE_KEY")

# ── MQTT setup ─────────────────────────────────────────────────────────
client = mqtt.Client(protocol=mqtt.MQTTv5)

if CA_CERT and CLIENT_CERT and PRIVATE_KEY:
    client.tls_set(ca_certs=CA_CERT, certfile=CLIENT_CERT, keyfile=PRIVATE_KEY)
else:
    if not (CA_CERT and CLIENT_CERT and PRIVATE_KEY):
        print("⚠️ TLS certificates not provided; using insecure MQTT", file=sys.stderr)

connected = False

def _on_connect(_client, _userdata, _flags, rc, *_args):
    global connected
    connected = rc == 0

client.on_connect = _on_connect

for attempt in range(1, 6):
    try:
        port = 8883 if CA_CERT and CLIENT_CERT and PRIVATE_KEY else 1883
        client.connect(IOT_ENDPOINT, port, 60)
        break
    except Exception as e:
        print(f"MQTT connect failed (try {attempt}/5): {e}", file=sys.stderr)
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


HEALTH_PORT = int(os.getenv("HEALTH_PORT", "8000"))

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

