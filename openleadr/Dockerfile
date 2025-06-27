FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV MQTT_TOPIC_METERING=volttron/metering
EXPOSE 8080
CMD ["python", "vtn_server.py"]


