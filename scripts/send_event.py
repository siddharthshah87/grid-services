#!/usr/bin/env python3
"""Publish a test OpenADR event via MQTT."""
import argparse
import json
import os
from datetime import datetime

import paho.mqtt.client as mqtt


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Publish a test OpenADR event to a VEN"
    )
    parser.add_argument("ven_id", help="Target VEN ID")
    parser.add_argument(
        "--host",
        default=os.getenv("IOT_ENDPOINT", "localhost"),
        help="MQTT broker host (default from IOT_ENDPOINT or localhost)",
    )
    parser.add_argument(
        "--port", type=int, default=1883, help="MQTT broker port"
    )
    args = parser.parse_args()

    event = {
        "event_id": "event1",
        "start_time": datetime.utcnow().isoformat(),
        "signal_name": "simple",
        "signal_type": "level",
        "signal_payload": 1,
        "targets": {"ven_id": args.ven_id},
        "response_required": "always",
    }

    client = mqtt.Client()
    client.connect(args.host, args.port, 60)
    topic = f"grid/event/{args.ven_id}"
    payload = json.dumps(event)
    client.publish(topic, payload)
    print(f"\U0001F4E1 Published event to {topic}: {payload}")
    client.disconnect()


if __name__ == "__main__":
    main()
