#!/usr/bin/env python3
"""Publish a test OpenADR event via MQTT."""
import argparse
import json
import os
import sys
from datetime import datetime

import paho.mqtt.client as mqtt


DEFAULT_IOT_ENDPOINT = "a1mgxpe8mg484j-ats.iot.us-west-2.amazonaws.com"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Publish a test OpenADR event to a VEN"
    )
    default_host = os.getenv("IOT_ENDPOINT", DEFAULT_IOT_ENDPOINT)

    def default_port_for_host(host: str) -> int:
        """Return the typical MQTT port for the given endpoint."""

        normalized_host = (host or "").lower()
        if normalized_host.endswith("amazonaws.com"):
            return 8883
        return 1883

    default_port = default_port_for_host(default_host)
    parser.add_argument("ven_id", help="Target VEN ID")
    parser.add_argument(
        "--host",
        default=default_host,
        help="MQTT broker host (default from IOT_ENDPOINT or AWS IoT endpoint)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=default_port,
        help=f"MQTT broker port (default {default_port})",
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
