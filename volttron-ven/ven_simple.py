#!/usr/bin/env python3
"""
Simplified VEN with thread-safe MQTT (mirrors backend pattern).

Goals:
1. Establish stable MQTT connection using gmqtt (async, thread-safe)
2. Subscribe to backend commands
3. Publish telemetry periodically
4. NO complex UI, NO device simulator initially
5. Prove connection stability first
"""
import asyncio
import json
import logging
import os
import ssl
import tempfile
import time
from datetime import datetime, timezone
from threading import Thread
import sys

import gmqtt
from gmqtt.mqtt.constants import MQTTv311
from flask import Flask, jsonify

# Force unbuffered output for logs
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Configuration from environment
VEN_ID = os.getenv("VEN_ID", "volttron_thing")

# Connection settings - match backend's simple approach
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "8883"))
MQTT_USE_TLS = os.getenv("MQTT_USE_TLS", "true").lower() == "true"
MQTT_KEEPALIVE = int(os.getenv("MQTT_KEEPALIVE", "60"))
REPORT_INTERVAL = int(os.getenv("REPORT_INTERVAL_SECONDS", "60"))

# Topics
TELEMETRY_TOPIC = f"ven/telemetry/{VEN_ID}"
BACKEND_CMD_TOPIC = f"ven/cmd/{VEN_ID}"

# Global state
current_power_kw = 10.0
shed_power_kw = 0.0
connected = False

# Flask app for health checks (runs in separate thread)
app = Flask(__name__)

@app.route('/health')
def health():
    """Health check endpoint for ECS."""
    return jsonify({"status": "healthy"}), 200

@app.route('/live')
def live():
    """Liveness check endpoint."""
    return jsonify({"status": "alive", "connected": connected}), 200

def run_flask():
    """Run Flask health check server in background thread"""
    app.run(host='0.0.0.0', port=8000, debug=False, use_reloader=False)


def _setup_tls_cert_file(cert_type: str) -> str | None:
    """Handle TLS certificates - either file paths or PEM content from environment."""
    env_var_map = {
        "ca_cert": ("CA_CERT_PEM", os.getenv("MQTT_CA_CERT")),
        "client_cert": ("CLIENT_CERT_PEM", os.getenv("MQTT_CLIENT_CERT")),
        "client_key": ("PRIVATE_KEY_PEM", os.getenv("MQTT_CLIENT_KEY")),
    }
    
    pem_env_var, config_path = env_var_map.get(cert_type, (None, None))
    
    # Prefer PEM content from environment variables
    if pem_env_var:
        pem_content = os.getenv(pem_env_var)
        if pem_content:
            try:
                temp_fd, temp_path = tempfile.mkstemp(suffix=f"_{cert_type}.pem")
                with os.fdopen(temp_fd, 'w') as temp_file:
                    temp_file.write(pem_content)
                logger.info(f"Created temporary {cert_type} file: {temp_path}")
                return temp_path
            except Exception as e:
                logger.error(f"Failed to create temporary {cert_type} file: {e}")
                if 'temp_fd' in locals() and temp_fd is not None:
                    os.close(temp_fd)
                return None

    # Fallback to file path
    if config_path and os.path.isfile(config_path):
        return config_path
    
    return config_path


def on_connect(client: gmqtt.Client, flags: dict, rc: int, properties) -> None:
    """Handle MQTT connection event."""
    global connected
    if rc != 0:
        logger.error(f"MQTT connection failed: rc={rc}")
        connected = False
        return
    
    connected = True
    logger.info(f"✅ MQTT connected (client_id={client._client_id})")
    
    # Subscribe to backend commands
    client.subscribe(BACKEND_CMD_TOPIC, qos=1)
    logger.info(f"📥 Subscribed to: {BACKEND_CMD_TOPIC}")


def on_disconnect(client: gmqtt.Client, packet, exc: Exception | None = None) -> None:
    """Handle MQTT disconnection."""
    global connected
    connected = False
    if exc:
        logger.warning(f"⚠️  MQTT disconnected unexpectedly: {exc}")
    else:
        logger.info("MQTT disconnected cleanly")


def on_message(client: gmqtt.Client, topic: str, payload: bytes, qos: int, properties) -> int:
    """Handle incoming MQTT messages."""
    logger.debug(f"📨 Message received on topic: {topic}")
    
    try:
        data = json.loads(payload.decode("utf-8"))
        logger.info(f"Backend command: {json.dumps(data, indent=2)}")
        
        # Handle commands
        op = data.get("op", "unknown")
        if op == "ping":
            logger.info("🏓 Received ping command")
            # TODO: Send acknowledgment
        elif op == "shedLoad":
            global shed_power_kw
            shed_power_kw = data.get("data", {}).get("amountKw", 0.0)
            logger.info(f"⚡ Shedding load: {shed_power_kw} kW")
        else:
            logger.info(f"Received command: op={op}")
            
    except Exception as e:
        logger.error(f"Error processing message: {e}")
    
    return 0


async def publish_telemetry(client: gmqtt.Client) -> None:
    """Publish telemetry periodically."""
    global current_power_kw, shed_power_kw
    
    while True:
        await asyncio.sleep(REPORT_INTERVAL)
        
        if not connected:
            logger.debug("Skipping telemetry - not connected")
            continue
        
        # Simulate varying load
        import random
        current_power_kw = max(1.0, current_power_kw + random.uniform(-0.5, 0.5))
        
        telemetry = {
            "schemaVersion": "1.0",
            "venId": VEN_ID,
            "timestamp": int(time.time()),
            "usedPowerKw": round(current_power_kw, 2),
            "shedPowerKw": round(shed_power_kw, 2),
            "batterySoc": 0.5,
            "loads": [
                {"id": "total", "currentPowerKw": round(current_power_kw, 2)}
            ]
        }
        
        try:
            client.publish(TELEMETRY_TOPIC, json.dumps(telemetry), qos=1)
            logger.info(f"📊 Published telemetry: {current_power_kw:.2f} kW (shed: {shed_power_kw:.3f} kW)")
        except Exception as e:
            logger.error(f"Failed to publish telemetry: {e}")


async def main() -> None:
    """Main entry point."""
    # Start Flask health check server in background thread
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("🏥 Health check server started on port 8000")
    
    logger.info("=" * 60)
    logger.info("🚀 Starting Simplified VEN (Thread-Safe MQTT)")
    logger.info("=" * 60)
    logger.info(f"VEN ID: {VEN_ID}")
    logger.info(f"MQTT Host: {MQTT_HOST}:{MQTT_PORT}")
    logger.info(f"TLS Enabled: {MQTT_USE_TLS}")
    logger.info(f"Report Interval: {REPORT_INTERVAL}s")
    logger.info(f"Telemetry Topic: {TELEMETRY_TOPIC}")
    logger.info(f"Command Topic: {BACKEND_CMD_TOPIC}")
    logger.info("=" * 60)
    
    # Create MQTT client
    client_id = f"{VEN_ID}_simple"
    client = gmqtt.Client(client_id)
    
    # Set callbacks
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    
    # Setup TLS
    ssl_context = None
    if MQTT_USE_TLS:
        ca_certs = _setup_tls_cert_file("ca_cert")
        certfile = _setup_tls_cert_file("client_cert")
        keyfile = _setup_tls_cert_file("client_key")
        
        if not ca_certs or not certfile or not keyfile:
            logger.error("❌ TLS certificates not properly configured")
            return
        
        ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=ca_certs)
        ssl_context.load_cert_chain(certfile=certfile, keyfile=keyfile)
        ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
        ssl_context.check_hostname = True  # Match backend's configuration
        
        logger.info(f"🔐 TLS configured (CA: {ca_certs})")
    
    # Connect to MQTT broker
    try:
        logger.info(f"🔗 Attempting connection to {MQTT_HOST}:{MQTT_PORT}...")
        logger.debug(f"SSL context: {ssl_context is not None}, TLS: {MQTT_USE_TLS}")
        await client.connect(
            MQTT_HOST,  # Connect directly to AWS IoT endpoint (like backend)
            MQTT_PORT,
            ssl=ssl_context or MQTT_USE_TLS,
            keepalive=MQTT_KEEPALIVE,
            version=MQTTv311
        )
        logger.info("🔗 Connection initiated, waiting for on_connect callback...")
        
        # Wait for connection to be established (up to 10 seconds)
        for i in range(20):
            if connected:
                logger.info("✅ Connection confirmed!")
                break
            await asyncio.sleep(0.5)
            if i % 4 == 0:
                logger.debug(f"Waiting for connection... ({i/2}s)")
        
        if not connected:
            logger.error("❌ Connection timeout - on_connect callback never fired")
            return
            
    except Exception as e:
        logger.error(f"❌ Failed to connect to {MQTT_HOST}:{MQTT_PORT}: {e}")
        logger.exception("Full traceback:")
        return
    
    # Start telemetry publishing task
    telemetry_task = asyncio.create_task(publish_telemetry(client))
    
    try:
        # Run forever
        await asyncio.Future()  # Run until cancelled
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down...")
    finally:
        telemetry_task.cancel()
        await client.disconnect()
        logger.info("✅ Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
