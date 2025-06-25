# openleadr/vtn_server.py
from openleadr import OpenADRServer
import paho.mqtt.client as mqtt
import json
import os
from datetime import datetime

MQTT_TOPIC_EVENTS = os.getenv("MQTT_TOPIC_EVENTS", "openadr/event")
MQTT_TOPIC_RESPONSES = os.getenv("MQTT_TOPIC_RESPONSES", "openadr/response")
IOT_ENDPOINT = os.getenv("IOT_ENDPOINT", "localhost")

# Set up MQTT client for publishing events and receiving responses
mqtt_client = mqtt.Client()
mqtt_client.connect(IOT_ENDPOINT, 1883, 60)

def _on_mqtt_message(client, userdata, msg):
    print(f"Response topic {msg.topic}: {msg.payload.decode()}")

mqtt_client.subscribe(MQTT_TOPIC_RESPONSES)
mqtt_client.on_message = _on_mqtt_message
mqtt_client.loop_start()

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
    print(f"Published event for {ven_id} to MQTT")

    return [event]

server.run()
