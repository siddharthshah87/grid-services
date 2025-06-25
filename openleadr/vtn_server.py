# openleadr/vtn_server.py
from openleadr import OpenADRServer
import os
import json
import paho.mqtt.client as mqtt

MQTT_TOPIC_METERING = os.getenv("MQTT_TOPIC_METERING", "volttron/metering")
IOT_ENDPOINT = os.getenv("IOT_ENDPOINT", "localhost")

server = OpenADRServer(vtn_id="my-vtn", http_port=8080)

metering_data = []

def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    print(f"Received metering data: {payload}")
    metering_data.append(json.loads(payload))

client = mqtt.Client()
client.on_message = on_message
client.connect(IOT_ENDPOINT, 1883, 60)
client.subscribe(MQTT_TOPIC_METERING)
client.loop_start()

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
    return []

server.run()
