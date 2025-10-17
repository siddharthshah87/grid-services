#!/usr/bin/env python3
"""
Minimal VEN - Just connect to AWS IoT Core and publish telemetry.
No health checks, no shadow sync, no complexity.
"""
import os
import json
import time
import random
import ssl
import paho.mqtt.client as mqtt

# Configuration from environment
IOT_ENDPOINT = os.getenv("IOT_ENDPOINT")
CLIENT_ID = os.getenv("CLIENT_ID", "volttron_local_minimal")
CA_CERT = os.getenv("CA_CERT", "./certs/ca.pem")
CLIENT_CERT = os.getenv("CLIENT_CERT", "./certs/client.crt")
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "./certs/client.key")
TELEMETRY_TOPIC = os.getenv("TELEMETRY_TOPIC", f"ven/telemetry/{CLIENT_ID}")
CMD_TOPIC = os.getenv("CMD_TOPIC", f"ven/cmd/{CLIENT_ID}")
ACK_TOPIC = os.getenv("ACK_TOPIC", f"ven/ack/{CLIENT_ID}")

# State
connected = False
message_count = 0

def on_connect(client, userdata, flags, rc):
    global connected
    if rc == 0:
        connected = True
        print(f"✅ Connected to AWS IoT Core (client_id={CLIENT_ID})")
        print(f"📡 Subscribing to command topic: {CMD_TOPIC}")
        client.subscribe(CMD_TOPIC, qos=1)
    else:
        connected = False
        print(f"❌ Connection failed with code {rc}")

def on_disconnect(client, userdata, rc):
    global connected
    connected = False
    if rc == 0:
        print("🔌 Disconnected (graceful)")
    else:
        print(f"⚠️  Disconnected unexpectedly (rc={rc})")

def on_message(client, userdata, msg):
    """Handle incoming commands"""
    try:
        payload = json.loads(msg.payload.decode())
        print(f"📨 Command received: {json.dumps(payload, indent=2)}")
        
        # Handle ping command
        if payload.get("op") == "ping":
            ack = {
                "op": "ping",
                "status": "success",
                "pong": True,
                "ts": int(time.time()),
                "correlationId": payload.get("correlationId")
            }
            client.publish(ACK_TOPIC, json.dumps(ack), qos=1)
            print(f"📤 Sent ack: {json.dumps(ack)}")
    except Exception as e:
        print(f"❌ Error processing message: {e}")

def simulate_power():
    """Simulate power consumption"""
    base = 10.0
    jitter = random.uniform(-1.0, 1.0)
    return round(base + jitter, 2)

def main():
    global message_count
    
    print("🚀 Starting Minimal VEN")
    print(f"   Endpoint: {IOT_ENDPOINT}")
    print(f"   Client ID: {CLIENT_ID}")
    print(f"   Telemetry Topic: {TELEMETRY_TOPIC}")
    print(f"   Command Topic: {CMD_TOPIC}")
    print(f"   Ack Topic: {ACK_TOPIC}")
    print()
    
    # Verify certificates exist
    for cert_name, cert_path in [("CA", CA_CERT), ("Client", CLIENT_CERT), ("Key", PRIVATE_KEY)]:
        if not os.path.exists(cert_path):
            print(f"❌ {cert_name} certificate not found: {cert_path}")
            return 1
        print(f"✓ {cert_name} cert: {cert_path}")
    print()
    
    # Create MQTT client
    client = mqtt.Client(client_id=CLIENT_ID, protocol=mqtt.MQTTv311)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    
    # Configure TLS
    try:
        client.tls_set(
            ca_certs=CA_CERT,
            certfile=CLIENT_CERT,
            keyfile=PRIVATE_KEY,
            cert_reqs=ssl.CERT_REQUIRED,
            tls_version=ssl.PROTOCOL_TLSv1_2
        )
        print("✓ TLS configured")
    except Exception as e:
        print(f"❌ TLS setup failed: {e}")
        return 1
    
    # Connect
    print(f"\n🔌 Connecting to {IOT_ENDPOINT}:8883...")
    try:
        client.connect(IOT_ENDPOINT, 8883, keepalive=60)
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return 1
    
    # Start network loop
    client.loop_start()
    
    # Wait for connection
    print("⏳ Waiting for connection...")
    for i in range(10):
        if connected:
            break
        time.sleep(1)
    
    if not connected:
        print("❌ Failed to connect after 10 seconds")
        client.loop_stop()
        return 1
    
    print("✅ Connection established!\n")
    print("📊 Publishing telemetry every 5 seconds...")
    print("Press Ctrl+C to stop\n")
    
    # Main loop - publish telemetry
    try:
        while True:
            if connected:
                message_count += 1
                power_kw = simulate_power()
                
                telemetry = {
                    "venId": CLIENT_ID,
                    "ts": int(time.time()),
                    "power_kw": power_kw,
                    "shed_kw": 0.0,
                    "message_num": message_count
                }
                
                result = client.publish(TELEMETRY_TOPIC, json.dumps(telemetry), qos=1)
                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    print(f"✓ [{message_count}] Published: {power_kw} kW (connected={connected})")
                else:
                    print(f"✗ [{message_count}] Publish failed: {result.rc}")
            else:
                print(f"⚠️  Not connected, waiting...")
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
    finally:
        client.loop_stop()
        client.disconnect()
        print("👋 Goodbye!")
    
    return 0

if __name__ == "__main__":
    exit(main())
