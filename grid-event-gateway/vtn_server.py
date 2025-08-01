"""Simple VTN server example used for development.

* Binds the OpenADR server to 0.0.0.0 so it is reachable from the ALB.
* Exposes /health on the same port so the ALB can mark targets healthy.
* Parses CERT_BUNDLE_JSON (3 PEM strings) and materialises them to files if
  provided. When unset the server falls back to an insecure MQTT connection,
  which is handy for local testing.
"""
from __future__ import annotations
import json
import os
import sys
import tempfile
import threading
import asyncio
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from aiohttp import web

# ── OpenAPI spec --------------------------------------------------------
OPENAPI_SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "OpenLEADR VTN Server", "version": "1.0.0"},
    "paths": {
        "/health": {
            "get": {
                "summary": "Health check",
                "responses": {
                    "200": {
                        "description": "Service healthy",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {"ok": {"type": "boolean"}},
                                }
                            }
                        },
                    }
                },
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

import paho.mqtt.client as mqtt
from openleadr import OpenADRServer

# Helper functions -------------------------------------------------------
def write_temp_file(data: str, suffix: str) -> str:
    """Write data to a temporary file and return its path."""
    if not data:
        raise ValueError("data must not be empty")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(data.encode())
    tmp.close()
    return tmp.name

def handle_event_request(ven_id: str, payload: dict):
    """Publish an event message and return a minimal OpenADR event."""
    message = {"ven_id": ven_id, **payload}
    mqttc.publish(MQTT_TOPIC_EVENTS, json.dumps(message))
    return [{"targets": {"ven_id": ven_id}, **payload}]

# ── ENV ------------------------------------------------------------------
MQTT_TOPIC_METERING  = os.getenv("MQTT_TOPIC_METERING", "volttron/metering")
MQTT_TOPIC_EVENTS    = os.getenv("MQTT_TOPIC_EVENTS",   "openadr/event")
MQTT_TOPIC_RESPONSES = os.getenv("MQTT_TOPIC_RESPONSES","openadr/response")
IOT_ENDPOINT         = os.getenv("IOT_ENDPOINT",        "localhost")
VENS_PORT            = int(os.getenv("VENS_PORT", 8081))

MQTT_PORT = int(
    os.getenv(
        "MQTT_PORT",
        "8883" if IOT_ENDPOINT != "localhost" else "1883",
    )
)

bundle_json = os.getenv("CERT_BUNDLE_JSON")
CA_CERT_PEM = CLIENT_CERT_PEM = PRIVATE_KEY_PEM = None
if bundle_json:
    try:
        bundle = json.loads(bundle_json)
        CA_CERT_PEM     = bundle["ca.crt"]
        CLIENT_CERT_PEM = bundle["client.crt"]
        PRIVATE_KEY_PEM = bundle["private.key"]
    except (json.JSONDecodeError, KeyError) as e:
        print(f"❌ Failed to parse CERT_BUNDLE_JSON: {e}", file=sys.stderr)
        sys.exit(1)
else:
    print("⚠️ CERT_BUNDLE_JSON not provided; using insecure MQTT connection", file=sys.stderr)

mqttc = mqtt.Client(protocol=mqtt.MQTTv5)

if CA_CERT_PEM and CLIENT_CERT_PEM and PRIVATE_KEY_PEM:
    # ── materialise PEM strings to disk ---------------------------------
    tmp_dir = tempfile.TemporaryDirectory(prefix="vtn_cert_")
    ca_path     = os.path.join(tmp_dir.name, "ca.crt")
    cert_path   = os.path.join(tmp_dir.name, "client.crt")
    key_path    = os.path.join(tmp_dir.name, "client.key")

    for content, path in [
        (CA_CERT_PEM, ca_path),
        (CLIENT_CERT_PEM, cert_path),
        (PRIVATE_KEY_PEM, key_path),
    ]:
        with open(path, "w") as f:
            f.write(content)

    print("📜 MQTT certs written to:")
    for p in (ca_path, cert_path, key_path):
        print(f"  - {p}")

    # Clean up temp files at exit
    import atexit
    import pathlib

    @atexit.register
    def _cleanup():
        for p in pathlib.Path(tmp_dir.name).glob("*"):
            p.unlink(missing_ok=True)
            print(f"🧹 Deleted temp cert: {p}")
        tmp_dir.cleanup()

    mqttc.tls_set(ca_certs=ca_path, certfile=cert_path, keyfile=key_path)

# ── MQTT client ----------------------------------------------------------
mqtt_connected = False

def _on_connect(_client, _userdata, _flags, rc, *_args):
    global mqtt_connected
    mqtt_connected = rc == 0

mqttc.on_connect = _on_connect

for attempt in range(1, 6):
    try:
        mqttc.connect(IOT_ENDPOINT, MQTT_PORT, keepalive=60)
        break
    except Exception as e:
        print(f"MQTT connect failed (try {attempt}/5): {e}", file=sys.stderr)
        time.sleep(min(2 ** attempt, 30))
mqttc.loop_start()

# ── Track registered VENs -----------------------------------------------
active_vens: set[str] = set()

async def ven_lookup(ven_id: str) -> bool:
    """Used by OpenADR to decide if a VEN is allowed to register."""
    return ven_id in active_vens

# ── Start OpenADR server -------------------------------------------------
vtn = OpenADRServer(vtn_id="myVtn", http_port=8080, http_host="0.0.0.0", ven_lookup=ven_lookup)

# ── Simple /health endpoint (same port 8080) -----------------------------
app = web.Application()
routes = web.RouteTableDef()

@routes.get("/openapi.json")
async def _openapi(_: web.Request):
    return web.json_response(OPENAPI_SPEC)

@routes.get("/docs")
async def _docs(_: web.Request):
    return web.Response(text=SWAGGER_HTML, content_type="text/html")

@routes.get("/health")
async def _health(_: web.Request):
    return web.json_response({"ok": mqtt_connected})

app.add_routes(routes)
vtn.app.add_routes(routes)

# ── VEN listing HTTP server (separate port) ------------------------------
class VenHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(sorted(active_vens)).encode())

def _start_ven_listing_server():
    HTTPServer(("0.0.0.0", VENS_PORT), VenHandler).serve_forever()

threading.Thread(target=_start_ven_listing_server, daemon=True).start()
print(f"🔎 VEN listing server started on port {VENS_PORT}")

# ── Main entry -----------------------------------------------------------
if __name__ == "__main__":
    print("********************************************************************************")
    print(" Starting VTN ‣ http://0.0.0.0:8080/OpenADR2/Simple/2.0b")
    print("********************************************************************************")
    asyncio.run(vtn.run())   # <-- key change: bind to 0.0.0.0

