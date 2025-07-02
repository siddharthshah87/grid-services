FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV MQTT_TOPIC_METERING=volttron/metering \
    CA_CERT=/certs/ca.crt \
    CLIENT_CERT=/certs/client.crt \
    PRIVATE_KEY=/certs/client.key \
    MQTT_PORT=8883
EXPOSE 8080
CMD ["python", "ven_agent.py"]

