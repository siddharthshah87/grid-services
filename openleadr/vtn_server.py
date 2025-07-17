"""Simple VTN server example used for development.

* Binds the OpenADR server to 0.0.0.0 so it is reachable from the ALB.
* Exposes /health on the same port so the ALB can mark targets healthy.
* Parses CERT_BUNDLE_JSON (3 PEM strings) and materialises them to files.
"""
from __future__ import annotations
import json, os, sys, ssl, tempfile, threading, asyncio
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

import paho.mqtt.client as mqtt
from openleadr import OpenADRServer

# ── ENV ------------------------------------------------------------------
MQTT_TOPIC_METERING  = os.getenv("MQTT_TOPIC_METERING", "volttron/metering")
MQTT_TOPIC_EVENTS    = os.getenv("MQTT_TOPIC_EVENTS",   "openadr/event")
MQTT_TOPIC_RESPONSES = os.getenv("MQTT_TOPIC_RESPONSES","openadr/response")
IOT_ENDPOINT         = os.getenv("IOT_ENDPOINT",        "localhost")
VENS_PORT            = int(os.getenv("VENS_PORT", 8081))

bundle_json = os.getenv("CERT_BUNDLE_JSON")
if bundle_json is None:
    print("❌ CERT_BUNDLE_JSON env var not set.", file=sys.stderr)
    sys.exit(1)

try:
    bundle = json.loads(bundle_json)
    CA_CERT_PEM     = bundle["ca.crt"]
    CLIENT_CERT_PEM = bundle["client.crt"]
    PRIVATE_KEY_PEM = bundle["private.key"]
except (json.JSONDecodeError, KeyError) as e:
    print(f"❌ Failed to parse CERT_BUNDLE_JSON: {e}", file=sys.stderr)
    sys.exit(1)

# ── materialise PEM strings to disk -------------------------------------
tmp_dir = tempfile.TemporaryDirectory(prefix="vtn_cert_")
ca_path     = os.path.join(tmp_dir.name, "ca.crt")
cert_path   = os.path.join(tmp_dir.name, "client.crt")
key_path    = os.path.join(tmp_dir.name, "client.key")

for content, path in [(CA_CERT_PEM, ca_path),
                      (CLIENT_CERT_PEM, cert_path),
                      (PRIVATE_KEY_PEM, key_path)]:
    with open(path, "w") as f:
        f.write(content)

print("📜 MQTT certs written to:")
for p in (ca_path, cert_path, key_path):
    print(f"  - {p}")

# Clean up temp files at exit
import atexit, pathlib
@atexit.register
def _cleanup():
    for p in pathlib.Path(tmp_dir.name).glob("*"):
        p.unlink(missing_ok=True)
        print(f"🧹 Deleted temp cert: {p}")
    tmp_dir.cleanup()

# ── MQTT client ----------------------------------------------------------
mqttc = mqtt.Client(protocol=mqtt.MQTTv5)
mqttc.tls_set(ca_certs=ca_path, certfile=cert_path, keyfile=key_path)
mqttc.connect(IOT_ENDPOINT, 8883, keepalive=60)
mqttc.loop_start()

# ── Track registered VENs -----------------------------------------------
active_vens: set[str] = set()

async def ven_lookup(ven_id: str) -> bool:
    """Used by OpenADR to decide if a VEN is allowed to register."""
    return ven_id in active_vens

# ── Start OpenADR server -------------------------------------------------
vtn = OpenADRServer(vtn_id="myVtn", http_port=8080, ven_lookup=ven_lookup)

# ── Simple /health endpoint (same port 8080) -----------------------------
from aiohttp import web
app = web.Application()
@app.get("/health")
async def _health(_: web.Request):
    return web.json_response({"ok": True})
vtn.app.add_get("/health", _health)

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
    asyncio.run(vtn.run(host="0.0.0.0"))   # <-- key change: bind to 0.0.0.0

