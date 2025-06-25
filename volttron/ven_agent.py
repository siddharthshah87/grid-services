# volttron/ven_agent.py
import time
import json
import paho.mqtt.client as mqtt
import os

MQTT_TOPIC_STATUS = os.getenv("MQTT_TOPIC_STATUS", "volttron/dev")
MQTT_TOPIC_EVENTS = os.getenv("MQTT_TOPIC_EVENTS", "openadr/event")
MQTT_TOPIC_RESPONSES = os.getenv("MQTT_TOPIC_RESPONSES", "openadr/response")
IOT_ENDPOINT = os.getenv("IOT_ENDPOINT", "localhost")

client = mqtt.Client()
client.connect(IOT_ENDPOINT, 1883, 60)

def on_event(client, userdata, msg):
    payload = json.loads(msg.payload.decode())
    print(f"Received event via MQTT: {payload}")
    response = {"ven_id": payload.get("ven_id"), "response": "ack"}
    client.publish(MQTT_TOPIC_RESPONSES, json.dumps(response))

client.subscribe(MQTT_TOPIC_EVENTS)
client.on_message = on_event
client.loop_start()

while True:
    client.publish(MQTT_TOPIC_STATUS, payload="{\"ven\": \"ready\"}", qos=1)
    print("Published VEN status to MQTT")
    time.sleep(10)

