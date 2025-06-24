:# volttron/Dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["python", "ven_agent.py"]

volttron/requirements.txt
#paho-mqtt
#requests

# volttron/ven_agent.py
import time
import paho.mqtt.client as mqtt
import os

MQTT_TOPIC = os.getenv("MQTT_TOPIC", "volttron/dev")
IOT_ENDPOINT = os.getenv("IOT_ENDPOINT", "localhost")

client = mqtt.Client()
client.connect(IOT_ENDPOINT, 1883, 60)

while True:
    client.publish(MQTT_TOPIC, payload="{\"ven\": \"ready\"}", qos=1)
    print("Published VEN status to MQTT")
    time.sleep(10)

