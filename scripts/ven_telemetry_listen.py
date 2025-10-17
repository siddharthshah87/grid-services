#!/usr/bin/env python3
"""Subscribe to VEN telemetry over AWS IoT Core (WebSocket + SigV4).

Examples:
  ./scripts/ven_telemetry_listen.py --ven-id volttron_minimal_unbuffered --endpoint a1...-ats.iot.us-west-2.amazonaws.com

Requires:
  pip install awscrt awsiotsdk
  AWS credentials (SSO, env, or shared config) with IoT permissions.
"""
import argparse
import json
import os
import sys
import threading

try:
    from awscrt import io, mqtt, auth
    from awsiot import mqtt_connection_builder
except Exception as e:
    print("This script requires awscrt and awsiotsdk. Install with: pip install awscrt awsiotsdk", file=sys.stderr)
    raise


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ven-id", required=True)
    ap.add_argument("--region", default=os.getenv("AWS_REGION", "us-west-2"))
    ap.add_argument("--endpoint", default=os.getenv("IOT_ENDPOINT"), help="ATS IoT Data endpoint (host only)")
    ap.add_argument("--client-id", default=None)
    args = ap.parse_args()

    if not args.endpoint:
        print("--endpoint or IOT_ENDPOINT env is required (ATS data endpoint)", file=sys.stderr)
        sys.exit(2)

    client_id = args.client_id or f"telemetry-listener-{args.ven_id}"
    topic = f"ven/telemetry/{args.ven_id}"

    elg = io.EventLoopGroup(1)
    resolver = io.DefaultHostResolver(elg)
    bootstrap = io.ClientBootstrap(elg, resolver)
    creds = auth.AwsCredentialsProvider.new_default_chain(bootstrap)

    conn = mqtt_connection_builder.websockets_with_default_aws_signing(
        endpoint=args.endpoint,
        client_bootstrap=bootstrap,
        region=args.region,
        credentials_provider=creds,
        client_id=client_id,
        clean_session=True,
        keep_alive_secs=60,
    )

    print(f"Connecting to wss://{args.endpoint} as {client_id}…")
    conn.connect().result()
    print(f"✅ Connected. Subscribing to: {topic}")

    stop = threading.Event()
    msg_count = [0]

    def on_telemetry(topic, payload, dup, qos, retain, **kwargs):
        msg_count[0] += 1
        try:
            msg = json.loads(payload.decode())
            print(f"\n[{msg_count[0]}] Telemetry received:")
            print(json.dumps(msg, indent=2))
        except Exception as e:
            print(f"\n[{msg_count[0]}] TELEMETRY (raw):", payload)
            print(f"Error: {e}")

    subscribe_future, _ = conn.subscribe(topic=topic, qos=mqtt.QoS.AT_LEAST_ONCE, callback=on_telemetry)
    subscribe_future.result()
    print("📡 Listening for telemetry... (Press Ctrl+C to stop)\n")

    try:
        stop.wait()
    except KeyboardInterrupt:
        pass
    finally:
        print("\nDisconnecting…")
        conn.disconnect().result()


if __name__ == "__main__":
    main()
