#!/usr/bin/env python3
"""Fetch the Thing Shadow reported state for a VEN.

Usage:
  ./scripts/ven_shadow_get.py --ven-id volttron_thing --endpoint a1...-ats.iot.us-west-2.amazonaws.com

Install: pip install boto3
"""
import argparse
import json
import os
import sys

try:
    import boto3
except Exception:
    print("Requires boto3. Install with: pip install boto3", file=sys.stderr)
    raise


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ven-id", required=True)
    ap.add_argument("--region", default=os.getenv("AWS_REGION", "us-west-2"))
    ap.add_argument("--endpoint", default=os.getenv("IOT_ENDPOINT"))
    args = ap.parse_args()

    if not args.endpoint:
        print("--endpoint or IOT_ENDPOINT env is required (ATS data endpoint)", file=sys.stderr)
        sys.exit(2)

    iotd = boto3.client("iot-data", region_name=args.region, endpoint_url=f"https://{args.endpoint}")
    resp = iotd.get_thing_shadow(thingName=args.ven_id)
    payload = json.loads(resp["payload"].read().decode())
    print(json.dumps(payload.get("state", {}).get("reported", payload), indent=2))


if __name__ == "__main__":
    main()

