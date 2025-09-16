#!/usr/bin/env python3
"""Publish a test OpenADR event via MQTT."""
import argparse
import json
import os
import sys
from datetime import datetime

import paho.mqtt.client as mqtt


DEFAULT_IOT_ENDPOINT = "vpce-0d3cb8ea5764b8097-r1j8w787.data.iot.us-west-2.vpce.amazonaws.com"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Publish a test OpenADR event to a VEN"
    )
    parser.add_argument("ven_id", help="Target VEN ID")
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
    if ca_cert and client_cert and private_key:
        client.tls_set(ca_certs=ca_cert, certfile=client_cert, keyfile=private_key)
    try:
        client.connect(args.host, args.port, 60)
    except Exception as e:
        print(
            f"❌ Failed to connect to MQTT broker at {args.host}:{args.port}: {e}"
        )
        sys.exit(1)
    topic = f"grid/event/{args.ven_id}"
    payload = json.dumps(event)
    client.publish(topic, payload)
    print(f"\U0001F4E1 Published event to {topic}: {payload}")
    client.disconnect()


if __name__ == "__main__":
    main()
