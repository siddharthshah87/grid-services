#!/usr/bin/env python3
"""Publish VEN backend commands over AWS IoT (boto3 iot-data).

Examples:
  ./scripts/ven_cmd_publish.py --ven-id volttron_thing --op setConfig \
    --data '{"report_interval_seconds":30,"target_power_kw":1.2}'

  ./scripts/ven_cmd_publish.py --ven-id volttron_thing --op shedLoad \
    --data '{"loadId":"ev1","reduceKw":2.0,"durationS":900,"eventId":"evt-9"}'

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
    ap.add_argument("--ven-id", required=True, help="VEN/Thing name")
    ap.add_argument("--region", default=os.getenv("AWS_REGION", "us-west-2"))
    ap.add_argument("--endpoint", default=os.getenv("IOT_ENDPOINT"), help="ATS IoT Data endpoint (host only)")
    ap.add_argument("--op", required=True, help="Command op: set|setConfig|setLoad|shedLoad|shedPanel|get|event|ping")
    ap.add_argument("--data", help="JSON data for the op")
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
    print(f"Published to {topic}:\n{json.dumps(payload, indent=2)}")


if __name__ == "__main__":
    main()

