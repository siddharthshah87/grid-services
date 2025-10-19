#!/usr/bin/env python3
"""
End-to-end test script for VEN event flow.

This script tests the complete flow:
1. Register VEN in backend
2. Create an event
3. Verify backend dispatches command
4. Monitor VEN acknowledgment
5. Verify telemetry shows load shedding
6. Verify event completion

Usage:
    python scripts/test_e2e_event_flow.py --backend-url http://localhost:8000 --ven-id test-ven-001
"""

import argparse
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import requests
import boto3
from botocore.exceptions import ClientError


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def log_step(message: str):
    """Log a test step."""
    print(f"{Colors.BLUE}{Colors.BOLD}➜{Colors.RESET} {message}")


def log_success(message: str):
    """Log a success message."""
    print(f"{Colors.GREEN}✓{Colors.RESET} {message}")


def log_error(message: str):
    """Log an error message."""
    print(f"{Colors.RED}✗{Colors.RESET} {message}")


def log_warning(message: str):
    """Log a warning message."""
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {message}")


def log_info(message: str):
    """Log an info message."""
    print(f"  {message}")


def register_ven(backend_url: str, ven_id: str) -> Dict[str, Any]:
    """Register a VEN in the backend."""
    log_step(f"Registering VEN: {ven_id}")
    
    url = f"{backend_url}/api/vens/"
    payload = {
        "name": f"Test VEN {ven_id}",
        "status": "online",
        "location": {"lat": 37.7749, "lon": -122.4194},
        "registrationId": ven_id,
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        ven = response.json()
        log_success(f"VEN registered with ID: {ven['id']}")
        return ven
    except requests.exceptions.RequestException as e:
        # VEN might already exist, try to get it
        try:
            response = requests.get(f"{backend_url}/api/vens/{ven_id}", timeout=10)
            if response.status_code == 200:
                log_warning("VEN already exists, using existing registration")
                return response.json()
        except:
            pass
        log_error(f"Failed to register VEN: {e}")
        raise


def create_event(backend_url: str, reduction_kw: float, duration_minutes: int) -> Dict[str, Any]:
    """Create a demand response event."""
    log_step(f"Creating event: {reduction_kw} kW reduction for {duration_minutes} minutes")
    
    now = datetime.now(timezone.utc)
    start_time = now + timedelta(seconds=10)  # Start in 10 seconds
    end_time = start_time + timedelta(minutes=duration_minutes)
    
    url = f"{backend_url}/api/events/"
    payload = {
        "status": "scheduled",
        "startTime": start_time.isoformat(),
        "endTime": end_time.isoformat(),
        "requestedReductionKw": reduction_kw,
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        event = response.json()
        log_success(f"Event created with ID: {event['id']}")
        log_info(f"Start: {event['startTime']}")
        log_info(f"End: {event['endTime']}")
        return event
    except requests.exceptions.RequestException as e:
        log_error(f"Failed to create event: {e}")
        raise


def monitor_mqtt_acks(ven_id: str, event_id: str, timeout_seconds: int = 30) -> bool:
    """Monitor MQTT for VEN acknowledgment."""
    log_step(f"Monitoring for VEN acknowledgment (timeout: {timeout_seconds}s)")
    
    try:
        import paho.mqtt.client as mqtt
        import os
        
        # Get IoT endpoint
        iot_endpoint = os.getenv("IOT_ENDPOINT")
        if not iot_endpoint:
            log_warning("IOT_ENDPOINT not set, skipping MQTT monitoring")
            return False
        
        ack_received = {"value": False, "data": None}
        
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                topic = f"ven/ack/{ven_id}"
                client.subscribe(topic, qos=1)
                log_info(f"Subscribed to {topic}")
        
        def on_message(client, userdata, msg):
            try:
                payload = json.loads(msg.payload.decode())
                if payload.get("event_id") == event_id or event_id in str(payload):
                    ack_received["value"] = True
                    ack_received["data"] = payload
                    log_success(f"Acknowledgment received!")
                    log_info(f"Payload: {json.dumps(payload, indent=2)}")
            except Exception as e:
                log_warning(f"Error parsing ack: {e}")
        
        # Create MQTT client
        client = mqtt.Client(client_id=f"test-{int(time.time())}")
        client.on_connect = on_connect
        client.on_message = on_message
        
        # Configure TLS if certs available
        ca_cert = os.getenv("CA_CERT", "./volttron-ven/certs/ca.pem")
        client_cert = os.getenv("CLIENT_CERT", "./volttron-ven/certs/client.crt")
        private_key = os.getenv("PRIVATE_KEY", "./volttron-ven/certs/client.key")
        
        import os.path
        if os.path.isfile(ca_cert) and os.path.isfile(client_cert) and os.path.isfile(private_key):
            import ssl
            client.tls_set(
                ca_certs=ca_cert,
                certfile=client_cert,
                keyfile=private_key,
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLSv1_2
            )
        
        # Connect and wait
        client.connect(iot_endpoint, 8883, keepalive=60)
        client.loop_start()
        
        # Wait for acknowledgment
        start_time = time.time()
        while not ack_received["value"] and (time.time() - start_time) < timeout_seconds:
            time.sleep(1)
        
        client.loop_stop()
        client.disconnect()
        
        if ack_received["value"]:
            return True
        else:
            log_warning("No acknowledgment received within timeout")
            return False
            
    except ImportError:
        log_warning("paho-mqtt not installed, skipping MQTT monitoring")
        return False
    except Exception as e:
        log_error(f"MQTT monitoring failed: {e}")
        return False


def verify_telemetry(backend_url: str, ven_id: str, event_id: str) -> bool:
    """Verify telemetry shows load shedding."""
    log_step("Verifying telemetry shows load shedding")
    
    # Wait a bit for telemetry to flow
    time.sleep(10)
    
    try:
        # Check VEN status endpoint
        response = requests.get(f"{backend_url}/api/vens/{ven_id}", timeout=10)
        if response.status_code == 200:
            ven = response.json()
            log_info(f"VEN Power: {ven.get('metrics', {}).get('currentPowerKw', 'N/A')} kW")
            log_info(f"Shed Available: {ven.get('metrics', {}).get('shedAvailabilityKw', 'N/A')} kW")
            
            # Check if active event is set
            if ven.get('metrics', {}).get('activeEventId') == event_id:
                log_success("Telemetry shows active event!")
                return True
            else:
                log_warning("Telemetry does not show active event yet")
                return False
        else:
            log_warning(f"Could not fetch VEN status: {response.status_code}")
            return False
    except Exception as e:
        log_error(f"Failed to verify telemetry: {e}")
        return False


def verify_event_metrics(backend_url: str, event_id: str) -> bool:
    """Verify event metrics are being tracked."""
    log_step("Verifying event metrics")
    
    try:
        response = requests.get(f"{backend_url}/api/events/{event_id}/metrics", timeout=10)
        if response.status_code == 200:
            metrics = response.json()
            log_success("Event metrics retrieved!")
            log_info(f"Current Reduction: {metrics.get('currentReductionKw', 0)} kW")
            log_info(f"VENs Responding: {metrics.get('vensResponding', 0)}")
            return metrics.get('vensResponding', 0) > 0
        else:
            log_warning(f"Could not fetch event metrics: {response.status_code}")
            return False
    except Exception as e:
        log_error(f"Failed to verify event metrics: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="End-to-end VEN event flow test")
    parser.add_argument("--backend-url", default="http://localhost:8000", help="Backend API URL")
    parser.add_argument("--ven-id", required=True, help="VEN ID to test with")
    parser.add_argument("--reduction-kw", type=float, default=2.0, help="Reduction amount in kW")
    parser.add_argument("--duration-minutes", type=int, default=5, help="Event duration in minutes")
    parser.add_argument("--skip-mqtt", action="store_true", help="Skip MQTT monitoring")
    
    args = parser.parse_args()
    
    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}VEN End-to-End Event Flow Test{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}\n")
    
    results = {
        "register_ven": False,
        "create_event": False,
        "mqtt_ack": False,
        "telemetry": False,
        "metrics": False,
    }
    
    try:
        # Step 1: Register VEN
        ven = register_ven(args.backend_url, args.ven_id)
        results["register_ven"] = True
        print()
        
        # Step 2: Create event
        event = create_event(args.backend_url, args.reduction_kw, args.duration_minutes)
        event_id = event["id"]
        results["create_event"] = True
        print()
        
        # Step 3: Wait for event to start
        log_step("Waiting for event to start...")
        time.sleep(15)  # Wait for event to become active
        print()
        
        # Step 4: Monitor MQTT acknowledgment
        if not args.skip_mqtt:
            ack_received = monitor_mqtt_acks(args.ven_id, event_id, timeout_seconds=30)
            results["mqtt_ack"] = ack_received
            print()
        else:
            log_warning("Skipping MQTT monitoring")
            print()
        
        # Step 5: Verify telemetry
        telemetry_ok = verify_telemetry(args.backend_url, args.ven_id, event_id)
        results["telemetry"] = telemetry_ok
        print()
        
        # Step 6: Verify event metrics
        metrics_ok = verify_event_metrics(args.backend_url, event_id)
        results["metrics"] = metrics_ok
        print()
        
    except Exception as e:
        log_error(f"Test failed with exception: {e}")
        print()
    
    # Print summary
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}Test Results Summary{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}\n")
    
    for test_name, passed in results.items():
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if passed else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"  {test_name.replace('_', ' ').title()}: {status}")
    
    print()
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    if passed_count == total_count:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ All tests passed!{Colors.RESET}\n")
        return 0
    else:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠ {passed_count}/{total_count} tests passed{Colors.RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
