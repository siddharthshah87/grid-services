"""Simple VTN server example used for development.

This file keeps track of all VENs that register with the VTN and exposes
an additional HTTP endpoint on a configurable port (`VENS_PORT`, default
8081) that lists those active VENs.
"""

from openleadr import OpenADRServer
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import threading
import os
import paho.mqtt.client as mqtt
import sys
import ssl
from datetime import datetime
import tempfile
import atexit
import asyncio
import time
import uuid

# MQTT topics and endpoint
MQTT_TOPIC_METERING = os.getenv("MQTT_TOPIC_METERING", "volttron/metering")
MQTT_TOPIC_EVENTS = os.getenv("MQTT_TOPIC_EVENTS", "openadr/event")
MQTT_TOPIC_RESPONSES = os.getenv("MQTT_TOPIC_RESPONSES", "openadr/response")
IOT_ENDPOINT = os.getenv("IOT_ENDPOINT", "localhost")
CERT_BUNDLE_JSON = os.getenv("CERT_BUNDLE_JSON")
KW_THRESHOLD = float(os.getenv("KW_THRESHOLD", "1.5"))
PRICE_TRIGGER = float(os.getenv("PRICE_TRIGGER", "0"))
SIGNAL_LEVEL = float(os.getenv("SIGNAL_LEVEL", "1"))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "5"))


if not CERT_BUNDLE_JSON:
    print("❌ CERT_BUNDLE_JSON env var not set.")
    sys.exit(1)

try:
    bundle = json.loads(CERT_BUNDLE_JSON)
    CA_CERT = bundle["ca.crt"]
    CLIENT_CERT = bundle["client.crt"]
    PRIVATE_KEY = bundle["private.key"]
except Exception as e:
    print(f"❌ Failed to parse CERT_BUNDLE_JSON: {e}")
    sys.exit(1)

# In-memory storage
metering_data = []
active_vens = set()
pending_ack = {}
acknowledged_events = {}

def write_temp_file(contents, suffix):
    if not contents or not contents.strip():
        raise ValueError(f"Attempted to write empty content to temp file with suffix {suffix}")
    temp_file = tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=suffix)
    temp_file.write(contents)
    temp_file.close()
    return temp_file.name

# MQTT setup
mqtt_client = mqtt.Client()

ca_cert_path = write_temp_file(CA_CERT, ".crt")
client_cert_path = write_temp_file(CLIENT_CERT, ".crt")
private_key_path = write_temp_file(PRIVATE_KEY, ".key")
print("📜 MQTT certs written to:")
print(f"  - CA: {ca_cert_path}")
print(f"  - Client: {client_cert_path}")
print(f"  - Key: {private_key_path}")

try:
    mqtt_client.tls_set(
        ca_certs=ca_cert_path,
        certfile=client_cert_path,
        keyfile=private_key_path
    )
except ssl.SSLError as e:
    print(f"❌ TLS setup failed: {e}")
    print("🔎 Check that your certificates are valid PEM-encoded files and not empty or corrupted.")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error during TLS setup: {e}")
    sys.exit(1)

try:
    mqtt_client.connect(IOT_ENDPOINT, 8883, 60)
except Exception as e:
    print(f"❌ Failed to connect to MQTT broker at {IOT_ENDPOINT}: {e}")
    sys.exit(1)

def on_metering_data(client, userdata, msg):
    payload = msg.payload.decode()
    print(f"📊 Received metering data: {payload}")
    try:
        metering_data.append(json.loads(payload))
    except json.JSONDecodeError:
        print("⚠️ Invalid JSON received in metering topic.")

def on_response(client, userdata, msg):
    payload = msg.payload.decode()
    print(f"📩 Response received on {msg.topic}: {payload}")
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        print("⚠️ Invalid JSON in response topic")
        return
    ven_id = data.get("ven_id")
    if ven_id and ven_id in pending_ack:
        event_id = pending_ack.pop(ven_id)
        acknowledged_events[event_id] = True
        print(f"✅ VEN {ven_id} acknowledged event {event_id}")

mqtt_client.subscribe(MQTT_TOPIC_METERING)
mqtt_client.subscribe(MQTT_TOPIC_RESPONSES)
mqtt_client.on_message = on_metering_data
mqtt_client.message_callback_add(MQTT_TOPIC_RESPONSES, on_response)
mqtt_client.loop_start()

# OpenADR server
server = OpenADRServer(vtn_id="my-vtn", http_port=8080)

def handle_registration(registration_info):
    ven_id = registration_info.get("ven_id", "ven123")
    active_vens.add(ven_id)
    print(f"✅ VEN registered: {ven_id}")
    return {
        "ven_id": ven_id,
        "registration_id": "reg123",
        "poll_interval": 10
    }

server.add_handler("on_create_party_registration", handle_registration)

def handle_cancel_registration(ven_id, registration_id):
    active_vens.discard(ven_id)
    print(f"❌ VEN unregistered: {ven_id}")
    return True
server.add_handler("on_cancel_party_registration", handle_cancel_registration)

def handle_event_request(ven_id, request):
    print(f"📥 Event request from {ven_id}: {request}")
    event_id = f"evt-{uuid.uuid4().hex[:8]}"
    event = {
        "event_id": event_id,
        "start_time": datetime.utcnow().isoformat(),
        "signal_name": "simple",
        "signal_type": "level",
        "signal_payload": SIGNAL_LEVEL,
        "targets": {"ven_id": ven_id},
        "response_required": "always",
    }

    mqtt_payload = json.dumps({"event": event})
    mqtt_client.publish(MQTT_TOPIC_EVENTS, mqtt_payload)
    for ven in active_vens:
        pending_ack[ven] = event_id
    acknowledged_events[event_id] = False
    print(f"📡 Published OpenADR event {event_id} for {ven_id} to {MQTT_TOPIC_EVENTS}")
    return [event]
server.add_handler("on_request_event", handle_event_request)

# Extra HTTP server to list active VENs
VENS_PORT = int(os.getenv("VENS_PORT", "8081"))


class VensHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/vens":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            payload = json.dumps(sorted(list(active_vens))).encode()
            self.wfile.write(payload)
        elif self.path == "/health":
            # Simple health check endpoint for the ALB
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_response(404)
            self.end_headers()

def metering_scheduler():
    while True:
        if metering_data:
            latest = metering_data[-1]
            power = latest.get("power_kw")
            price = latest.get("price")
            if power is not None and power >= KW_THRESHOLD:
                event_id = f"evt-{uuid.uuid4().hex[:8]}"
                event = {
                    "event_id": event_id,
                    "start_time": datetime.utcnow().isoformat(),
                    "signal_name": "simple",
                    "signal_type": "level",
                    "signal_payload": SIGNAL_LEVEL,
                    "targets": {"ven_id": "all"},
                    "response_required": "always",
                }
                mqtt_client.publish(MQTT_TOPIC_EVENTS, json.dumps({"event": event}))
                for ven in active_vens:
                    pending_ack[ven] = event_id
                acknowledged_events[event_id] = False
                print(f"⚡ Threshold exceeded ({power} kW). Event {event_id} sent")
        time.sleep(CHECK_INTERVAL)

def run_vens_server():
    httpd = HTTPServer(("0.0.0.0", VENS_PORT), VensHandler)
    print(f"🔎 VEN listing server started on port {VENS_PORT}")
    httpd.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_vens_server, daemon=True).start()
    threading.Thread(target=metering_scheduler, daemon=True).start()
    
    def cleanup_temp_certs():
        for path in [ca_cert_path, client_cert_path, private_key_path]:
            try:
                os.remove(path)
                print(f"🧹 Deleted temp cert: {path}")
            except Exception as e:
                print(f"⚠️ Failed to delete temp file {path}: {e}")

    atexit.register(cleanup_temp_certs)
    asyncio.run(server.run())

