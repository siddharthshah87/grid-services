#!/usr/bin/env python3
"""Subscribe to VEN responses via MQTT and print them."""
import argparse
import os
import sys
import paho.mqtt.client as mqtt


DEFAULT_IOT_ENDPOINT = "vpce-0d3cb8ea5764b8097-r1j8w787.data.iot.us-west-2.vpce.amazonaws.com"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Monitor MQTT responses from a VEN"
    )
    parser.add_argument("ven_id", help="VEN ID to monitor")
    parser.add_argument(
        "--host",
        default=os.getenv("IOT_ENDPOINT", DEFAULT_IOT_ENDPOINT),
        help="MQTT broker host (default from IOT_ENDPOINT or AWS IoT endpoint)",
    )
    parser.add_argument(
        "--port", type=int, default=1883, help="MQTT broker port"
    )
    ca_cert = os.getenv("CA_CERT")
    client_cert = os.getenv("CLIENT_CERT")
    private_key = os.getenv("PRIVATE_KEY")
    args = parser.parse_args()

    topic = f"grid/response/{args.ven_id}"
    client = mqtt.Client()
    if ca_cert and client_cert and private_key:
        client.tls_set(ca_certs=ca_cert, certfile=client_cert, keyfile=private_key)

    def on_message(client, userdata, msg):
        print(f"{msg.topic}: {msg.payload.decode()}")

    client.on_message = on_message
    try:
        client.connect(args.host, args.port, 60)
    except Exception as e:
        print(f"❌ Failed to connect to MQTT broker at {args.host}:{args.port}: {e}")
        sys.exit(1)
    client.subscribe(topic)
    print(f"\U0001F50D Subscribed to {topic}. Press Ctrl+C to exit.")
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
