# volttron/ven_agent.py
import os, json, random, time, sys, signal, tempfile, pathlib
import paho.mqtt.client as mqtt

# ── helpers ────────────────────────────────────────────────────────────
def _materialise_pem(var_name: str) -> str | None:
    """Return a file-path ready for paho.tls_set()."""
    val = os.getenv(var_name)
    if not val:
        return None

    if val.startswith("-----BEGIN"):                     # looks like PEM
        pem_path = pathlib.Path(tempfile.gettempdir()) / f"{var_name.lower()}.pem"
        pem_path.write_text(val)
        os.environ[var_name] = str(pem_path)             # mutate for later debug
        return str(pem_path)

    return val                                           # already a path

# ── env / config ───────────────────────────────────────────────────────
MQTT_TOPIC_STATUS     = os.getenv("MQTT_TOPIC_STATUS", "volttron/dev")
MQTT_TOPIC_EVENTS     = os.getenv("MQTT_TOPIC_EVENTS", "openadr/event")
MQTT_TOPIC_RESPONSES  = os.getenv("MQTT_TOPIC_RESPONSES", "openadr/response")
MQTT_TOPIC_METERING   = os.getenv("MQTT_TOPIC_METERING", "volttron/metering")
IOT_ENDPOINT          = os.getenv("IOT_ENDPOINT", "localhost")

CA_CERT     = _materialise_pem("CA_CERT")
CLIENT_CERT = _materialise_pem("CLIENT_CERT")
PRIVATE_KEY = _materialise_pem("PRIVATE_KEY")

# ── MQTT setup ─────────────────────────────────────────────────────────
client = mqtt.Client(protocol=mqtt.MQTTv5)

if CA_CERT and CLIENT_CERT and PRIVATE_KEY:
    client.tls_set(ca_certs=CA_CERT,
                   certfile=CLIENT_CERT,
                   keyfile=PRIVATE_KEY)

try:
    client.connect(IOT_ENDPOINT, 8883, 60)
except Exception as e:
    print(f"❌ Failed to connect to MQTT broker at {IOT_ENDPOINT}: {e}", file=sys.stderr)
    sys.exit(1)

# ── graceful shutdown ─────────────────────────────────────────────────
def _shutdown(signo, _frame):
    print("Received SIGTERM, disconnecting cleanly…")
    client.loop_stop()
    client.disconnect()
    sys.exit(0)

signal.signal(signal.SIGTERM, _shutdown)

client.loop_start()

# ── message handler ────────────────────────────────────────────────────
def on_event(_client, _userdata, msg):
    payload = json.loads(msg.payload.decode())
    print(f"Received event via MQTT: {payload}")
    response = {"ven_id": payload.get("ven_id", "ven123"), "response": "ack"}
    client.publish(MQTT_TOPIC_RESPONSES, json.dumps(response), qos=1)

# ── main loop ──────────────────────────────────────────────────────────
def main(iterations: int | None = None) -> None:
    client.subscribe(MQTT_TOPIC_EVENTS)
    client.on_message = on_event

    count = 0
    while True:
        client.publish(MQTT_TOPIC_STATUS,   json.dumps({"ven": "ready"}), qos=1)
        client.publish(MQTT_TOPIC_METERING, json.dumps({
            "timestamp": int(time.time()),
            "power_kw": round(random.uniform(0.5, 2.0), 2),
        }), qos=1)
        print("Published VEN status and metering data to MQTT")

        count += 1
        if iterations is not None and count >= iterations:
            break
        time.sleep(10)

if __name__ == "__main__":
    main()

