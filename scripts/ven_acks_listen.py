#!/usr/bin/env python3
"""Subscribe to VEN acks over AWS IoT Core (WebSocket + SigV4).

Examples:
  ./scripts/ven_acks_listen.py --ven-id volttron_thing --endpoint a1...-ats.iot.us-west-2.amazonaws.com

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
    ap.add_argument("--filter-corr", default=None, help="Only print acks matching correlationId")
    ap.add_argument("--client-id", default=None)
    args = ap.parse_args()

    if not args.endpoint:
        print("--endpoint or IOT_ENDPOINT env is required (ATS data endpoint)", file=sys.stderr)
        sys.exit(2)

    client_id = args.client_id or f"acks-listener-{args.ven_id}"
    topic = f"ven/ack/{args.ven_id}"

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
    print("Connected. Subscribing to:", topic)

    stop = threading.Event()

    def on_ack(topic, payload, dup, qos, retain, **kwargs):
        try:
            msg = json.loads(payload.decode())
        except Exception:
            print("ACK (raw):", payload)
            return
        if args.filter_corr and str(msg.get("correlationId")) != args.filter_corr:
            return
        print(json.dumps(msg, indent=2))

    subscribe_future, _ = conn.subscribe(topic=topic, qos=mqtt.QoS.AT_LEAST_ONCE, callback=on_ack)
    subscribe_future.result()

    try:
        stop.wait()
    except KeyboardInterrupt:
        pass
    finally:
        print("Disconnecting…")
        conn.disconnect().result()


if __name__ == "__main__":
    main()

