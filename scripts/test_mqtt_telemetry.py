#!/usr/bin/env python3
"""Test MQTT telemetry message for VEN registration."""
import json
import sys
import paho.mqtt.client as mqtt
import time

# MQTT configuration for AWS IoT Core
IOT_ENDPOINT = "a1mgxpe8mg484j-ats.iot.us-west-2.amazonaws.com"
TOPIC = "volttron/metering"

def main():
    # Sample telemetry payload that matches what VOLTTRON VEN sends
    telemetry_payload = {
        "venId": "volttron_thing",
        "timestamp": int(time.time()),
        "usedPowerKw": 11.36,
        "shedPowerKw": 0.0,
        "batterySoc": 0.5,
        "loads": [
            {
                "id": "hvac1",
                "currentPowerKw": 2.48,
                "capacityKw": 3.5,
                "shedCapabilityKw": 0.0,
                "type": "hvac",
                "name": "HVAC"
            },
            {
                "id": "ev1", 
                "currentPowerKw": 7.2,
                "capacityKw": 7.2,
                "shedCapabilityKw": 7.2,
                "type": "ev",
                "name": "EV Charger"
            }
        ]
    }
    
    client = mqtt.Client()
    
    # For AWS IoT Core, we'd need certificates, but let's first test locally
    # This is just to show the expected message format
    print("Sample telemetry payload that would trigger auto-registration:")
    print(json.dumps(telemetry_payload, indent=2))
    print(f"\nWould be published to topic: {TOPIC}")

if __name__ == "__main__":
    main()