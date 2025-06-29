#!/usr/bin/env python3
"""Subscribe to VEN responses via MQTT and print them."""
import argparse
import os
import paho.mqtt.client as mqtt


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Monitor MQTT responses from a VEN"
    )
    parser.add_argument("ven_id", help="VEN ID to monitor")
    parser.add_argument(
        "--host",
        default=os.getenv("IOT_ENDPOINT", "localhost"),
        help="MQTT broker host (default from IOT_ENDPOINT or localhost)",
    )
    parser.add_argument(
        "--port", type=int, default=1883, help="MQTT broker port"
    )
    args = parser.parse_args()

    topic = f"grid/response/{args.ven_id}"
    client = mqtt.Client()

    def on_message(client, userdata, msg):
        print(f"{msg.topic}: {msg.payload.decode()}")

    client.on_message = on_message
    client.connect(args.host, args.port, 60)
    client.subscribe(topic)
    print(f"\U0001F50D Subscribed to {topic}. Press Ctrl+C to exit.")
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
