# volttron/ven_agent.py
import time
import json
import random
import paho.mqtt.client as mqtt
import os

MQTT_TOPIC = os.getenv("MQTT_TOPIC", "volttron/dev")
MQTT_TOPIC_METERING = os.getenv("MQTT_TOPIC_METERING", "volttron/metering")
IOT_ENDPOINT = os.getenv("IOT_ENDPOINT", "localhost")

client = mqtt.Client()
client.connect(IOT_ENDPOINT, 1883, 60)
client.loop_start()

while True:
    client.publish(MQTT_TOPIC, payload="{\"ven\": \"ready\"}", qos=1)
    meter_payload = {
        "timestamp": int(time.time()),
        "power_kw": round(random.uniform(0.5, 2.0), 2)
    }
    client.publish(MQTT_TOPIC_METERING, payload=json.dumps(meter_payload), qos=1)
    print("Published VEN status and metering data to MQTT")
    time.sleep(10)

