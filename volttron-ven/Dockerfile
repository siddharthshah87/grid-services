# ──────────────────────────────────────────────────────────────────────
# volttron-ven  |  build image tag v0.4.2
# ──────────────────────────────────────────────────────────────────────
FROM python:3.10-slim

# ---- system deps (tiny image, so keep it lean) -----------------------
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# ---- python deps -----------------------------------------------------
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- application code ------------------------------------------------
COPY . .

# ---- runtime ENV with *safe* defaults --------------------------------
# These are only fallbacks; ECS will override them with Secrets Manager
ENV MQTT_TOPIC_METERING=volttron/metering \
    MQTT_TOPIC_EVENTS=openadr/event \
    MQTT_TOPIC_RESPONSES=openadr/response \
    MQTT_TOPIC_STATUS=volttron/dev \
    IOT_ENDPOINT=localhost

# ---- entry-point -----------------------------------------------------
# Writes PEM strings from env vars to /tmp/ven/*.pem and launches agent
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8080
ENTRYPOINT ["/entrypoint.sh"]

