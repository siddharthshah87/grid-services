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
from datetime import datetime

# MQTT topics and endpoint
MQTT_TOPIC_METERING = os.getenv("MQTT_TOPIC_METERING", "volttron/metering")
MQTT_TOPIC_EVENTS = os.getenv("MQTT_TOPIC_EVENTS", "openadr/event")
MQTT_TOPIC_RESPONSES = os.getenv("MQTT_TOPIC_RESPONSES", "openadr/response")
IOT_ENDPOINT = os.getenv("IOT_ENDPOINT", "localhost")
CA_CERT = os.getenv("CA_CERT")
CLIENT_CERT = os.getenv("CLIENT_CERT")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

# In-memory storage
metering_data = []
active_vens = set()

# MQTT setup
mqtt_client = mqtt.Client()
if CA_CERT and CLIENT_CERT and PRIVATE_KEY:
    mqtt_client.tls_set(ca_certs=CA_CERT, certfile=CLIENT_CERT, keyfile=PRIVATE_KEY)

def on_metering_data(client, userdata, msg):
    payload = msg.payload.decode()
    print(f"📊 Received metering data: {payload}")
    try:
        metering_data.append(json.loads(payload))
    except json.JSONDecodeError:
        print("⚠️ Invalid JSON received in metering topic.")

def on_response(client, userdata, msg):
    print(f"📩 Response received on {msg.topic}: {msg.payload.decode()}")

mqtt_client.connect(IOT_ENDPOINT, 8883, 60)
mqtt_client.subscribe(MQTT_TOPIC_METERING)
mqtt_client.subscribe(MQTT_TOPIC_RESPONSES)
mqtt_client.on_message = on_metering_data
mqtt_client.message_callback_add(MQTT_TOPIC_RESPONSES, on_response)
mqtt_client.loop_start()

# OpenADR server
server = OpenADRServer(vtn_id="my-vtn", http_port=8080)

@server.add_handler("on_create_party_registration")
def handle_registration(registration_info):
    ven_id = registration_info.get("ven_id", "ven123")
    active_vens.add(ven_id)
    print(f"✅ VEN registered: {ven_id}")
    return {
        "ven_id": ven_id,
        "registration_id": "reg123",
        "poll_interval": 10
    }

@server.add_handler("on_cancel_party_registration")
def handle_cancel_registration(ven_id, registration_id):
    active_vens.discard(ven_id)
    print(f"❌ VEN unregistered: {ven_id}")
    return True

@server.add_handler("on_request_event")
def handle_event_request(ven_id, request):
    print(f"📥 Event request from {ven_id}: {request}")
    event = {
        "event_id": "event1",
        "start_time": datetime.utcnow().isoformat(),
        "signal_name": "simple",
        "signal_type": "level",
        "signal_payload": 1,
        "targets": {"ven_id": ven_id},
        "response_required": "always",
    }

    mqtt_payload = json.dumps({"ven_id": ven_id, "event": event})
    mqtt_client.publish(MQTT_TOPIC_EVENTS, mqtt_payload)
    print(f"📡 Published OpenADR event for {ven_id} to {MQTT_TOPIC_EVENTS}")
    return [event]

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

def run_vens_server():
    httpd = HTTPServer(("0.0.0.0", VENS_PORT), VensHandler)
    print(f"🔎 VEN listing server started on port {VENS_PORT}")
    httpd.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_vens_server, daemon=True).start()
    server.run()
