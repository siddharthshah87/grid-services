# grid-event-gateway/Dockerfile
FROM python:3.10-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV MQTT_TOPIC_METERING=volttron/metering \
    MQTT_TOPIC_EVENTS=openadr/event \
    MQTT_TOPIC_RESPONSES=openadr/response \
    IOT_ENDPOINT=vpce-0d3cb8ea5764b8097-r1j8w787.data.iot.us-west-2.vpce.amazonaws.com \
    VENS_PORT=8081
EXPOSE 8080
EXPOSE 8081

CMD ["python", "vtn_server.py"]

