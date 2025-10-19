#!/usr/bin/env python3
"""Publish VEN backend commands over AWS IoT (boto3 iot-data).

Examples:
  # Dispatch DR event with load shedding
  ./scripts/ven_cmd_publish.py --ven-id volttron_thing --op event \
    --shed-kw 2.0 --duration 300 --event-id evt-test-001

  # Send generic command with custom data
  ./scripts/ven_cmd_publish.py --ven-id volttron_thing --op setConfig \
    --data '{"report_interval_seconds":30,"target_power_kw":1.2}'

  # Restore command
  ./scripts/ven_cmd_publish.py --ven-id volttron_thing --op restore

Requires AWS credentials and the IoT Data ATS endpoint. Set via:
  - env IOT_ENDPOINT (e.g. a1xxxxxxxxx-ats.iot.us-west-2.amazonaws.com)
  - or pass --endpoint

Install: pip install boto3
"""
import argparse
import json
import os
import sys
import time

try:
    import boto3
except Exception as e:
    print("This script requires boto3. Install with: pip install boto3", file=sys.stderr)
    raise


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ven-id", required=True, help="VEN/Thing name (e.g., volttron_thing)")
    ap.add_argument("--region", default=os.getenv("AWS_REGION", "us-west-2"))
    ap.add_argument("--endpoint", default=os.getenv("IOT_ENDPOINT"), help="ATS IoT Data endpoint (host only)")
    ap.add_argument("--op", required=True, help="Command op: event|restore|setConfig|ping")
    ap.add_argument("--shed-kw", type=float, help="For 'event' op: kW to shed")
    ap.add_argument("--duration", type=int, help="For 'event' op: duration in seconds")
    ap.add_argument("--event-id", help="For 'event' op: event ID")
    ap.add_argument("--data", help="JSON data for the op (alternative to specific flags)")
    ap.add_argument("--corr-id", default=None, help="Correlation ID to include in the command")
    args = ap.parse_args()

    if not args.endpoint:
        print("--endpoint or IOT_ENDPOINT env is required (ATS data endpoint)", file=sys.stderr)
        sys.exit(2)

    payload: dict = {
        "op": args.op,
        "venId": args.ven_id,
        "correlationId": args.corr_id or f"corr-{int(time.time())}",
    }
    
    # Handle 'event' operation with specific parameters
    if args.op == "event":
        if not args.shed_kw or not args.duration:
            print("For 'event' op, --shed-kw and --duration are required", file=sys.stderr)
            sys.exit(2)
        payload["shed_kw"] = args.shed_kw
        payload["duration_sec"] = args.duration
        payload["event_id"] = args.event_id or f"evt-{int(time.time())}"
    
    # Add custom data if provided
    if args.data:
        try:
            payload["data"] = json.loads(args.data)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON for --data: {e}", file=sys.stderr)
            sys.exit(2)

    iotd = boto3.client(
        "iot-data",
        region_name=args.region,
        endpoint_url=f"https://{args.endpoint}",
    )

    topic = f"ven/cmd/{args.ven_id}"
    iotd.publish(topic=topic, qos=1, payload=json.dumps(payload).encode("utf-8"))
    print(f"✅ Published to {topic}:")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()


