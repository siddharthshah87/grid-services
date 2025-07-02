# volttron/ven_agent.py
import time
import json
import random
import os
import paho.mqtt.client as mqtt
import sys

# MQTT topics and endpoint from environment variables
MQTT_TOPIC_STATUS = os.getenv("MQTT_TOPIC_STATUS", "volttron/dev")
MQTT_TOPIC_EVENTS = os.getenv("MQTT_TOPIC_EVENTS", "openadr/event")
MQTT_TOPIC_RESPONSES = os.getenv("MQTT_TOPIC_RESPONSES", "openadr/response")
MQTT_TOPIC_METERING = os.getenv("MQTT_TOPIC_METERING", "volttron/metering")
IOT_ENDPOINT = os.getenv("IOT_ENDPOINT", "localhost")
CA_CERT = os.getenv("CA_CERT")
CLIENT_CERT = os.getenv("CLIENT_CERT")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

# Setup MQTT client
client = mqtt.Client()
if CA_CERT and CLIENT_CERT and PRIVATE_KEY:
    client.tls_set(ca_certs=CA_CERT, certfile=CLIENT_CERT, keyfile=PRIVATE_KEY)
try:
    client.connect(IOT_ENDPOINT, 8883, 60)
except Exception as e:
    print(f"❌ Failed to connect to MQTT broker at {IOT_ENDPOINT}: {e}")
    sys.exit(1)
client.loop_start()

# Event handler for incoming OpenADR events
def on_event(client, userdata, msg):
    payload = json.loads(msg.payload.decode())
    print(f"Received event via MQTT: {payload}")
    response = {
        "ven_id": payload.get("ven_id", "ven123"),
        "response": "ack"
    }
    client.publish(MQTT_TOPIC_RESPONSES, json.dumps(response))

client.subscribe(MQTT_TOPIC_EVENTS)
client.on_message = on_event

# Main loop: publish status and metering data every 10s
while True:
    client.publish(MQTT_TOPIC_STATUS, payload=json.dumps({"ven": "ready"}), qos=1)
    meter_payload = {
        "timestamp": int(time.time()),
        "power_kw": round(random.uniform(0.5, 2.0), 2)
    }
    client.publish(MQTT_TOPIC_METERING, payload=json.dumps(meter_payload), qos=1)
    print("Published VEN status and metering data to MQTT")
    time.sleep(10)
