# openleadr/vtn_server.py
from openleadr import OpenADRServer
import json
import os
from datetime import datetime
import paho.mqtt.client as mqtt

# Environment variables for MQTT topics and broker
MQTT_TOPIC_METERING = os.getenv("MQTT_TOPIC_METERING", "volttron/metering")
MQTT_TOPIC_EVENTS = os.getenv("MQTT_TOPIC_EVENTS", "openadr/event")
MQTT_TOPIC_RESPONSES = os.getenv("MQTT_TOPIC_RESPONSES", "openadr/response")
IOT_ENDPOINT = os.getenv("IOT_ENDPOINT", "localhost")

# In-memory store for incoming metering data
metering_data = []

# MQTT client to receive metering data and responses, and publish events
mqtt_client = mqtt.Client()

def on_metering_data(client, userdata, msg):
    payload = msg.payload.decode()
    print(f"Received metering data: {payload}")
    try:
        metering_data.append(json.loads(payload))
    except json.JSONDecodeError:
        print("⚠️ Invalid JSON received in metering topic.")

def on_response(client, userdata, msg):
    print(f"Response received on {msg.topic}: {msg.payload.decode()}")

mqtt_client.on_message = on_metering_data
mqtt_client.connect(IOT_ENDPOINT, 1883, 60)
mqtt_client.subscribe(MQTT_TOPIC_METERING)
mqtt_client.message_callback_add(MQTT_TOPIC_RESPONSES, on_response)
mqtt_client.subscribe(MQTT_TOPIC_RESPONSES)
mqtt_client.loop_start()

# OpenADR VTN setup
server = OpenADRServer(vtn_id="my-vtn", http_port=8080)

@server.add_handler("on_create_party_registration")
def handle_registration(registration_info):
    return {
        "ven_id": registration_info.get("ven_id", "ven123"),
        "registration_id": "reg123",
        "poll_interval": 10
    }

@server.add_handler("on_request_event")
def handle_event_request(ven_id, request):
    print(f"Request from {ven_id}: {request}")
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

# Start the VTN server
server.run()
