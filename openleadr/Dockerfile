# openleadr/Dockerfile
FROM python:3.10-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV MQTT_TOPIC_METERING=volttron/metering \
    MQTT_TOPIC_EVENTS=openadr/event \
    MQTT_TOPIC_RESPONSES=openadr/response \
    IOT_ENDPOINT=localhost \
    CA_CERT=/certs/ca.crt \
    CLIENT_CERT=/certs/client.crt \
<<<<<<< Updated upstream
    PRIVATE_KEY=/certs/client.key \
    VENS_PORT=8081
=======
    PRIVATE_KEY=/certs/client.key

>>>>>>> Stashed changes
EXPOSE 8080
EXPOSE 8081

CMD ["python", "vtn_server.py"]

