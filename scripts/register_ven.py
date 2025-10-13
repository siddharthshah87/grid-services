#!/usr/bin/env python3
"""Register a new VEN in the backend database."""
import argparse
import json
import requests
import sys

def main():
    parser = argparse.ArgumentParser(description="Register a VEN in the backend database")
    parser.add_argument("--backend-url", default="backend-alb-948465488.us-west-2.elb.amazonaws.com", 
                       help="Backend API URL")
    parser.add_argument("--ven-id", required=True, help="VEN ID to register")
    parser.add_argument("--name", help="Display name for the VEN")
    parser.add_argument("--lat", type=float, default=37.7749, help="Latitude")
    parser.add_argument("--lon", type=float, default=-122.4194, help="Longitude")
    parser.add_argument("--status", default="online", help="Initial status")
    
    args = parser.parse_args()
    
    # Prepare payload
    payload = {
        "name": args.name or f"VEN {args.ven_id}",
        "status": args.status,
        "location": {
            "lat": args.lat,
            "lon": args.lon
        },
        "registrationId": args.ven_id
    }
    
    # Make API call
    url = f"http://{args.backend_url}/api/vens/"
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ Successfully registered VEN: {result['id']}")
        print(json.dumps(result, indent=2))
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to register VEN: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"Error details: {json.dumps(error_detail, indent=2)}")
            except:
                print(f"Response text: {e.response.text}")
        sys.exit(1)

if __name__ == "__main__":
    main()