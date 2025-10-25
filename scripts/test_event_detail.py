#!/usr/bin/env python3
"""
Quick script to test event detail endpoint locally.
Usage: python scripts/test_event_detail.py <event_id>
"""
import sys
import requests

def test_event_detail(backend_url: str, event_id: str):
    """Test fetching event details from the backend."""
    url = f"{backend_url}/api/events/{event_id}"
    print(f"Testing: {url}")
    print("-" * 60)
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print("-" * 60)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success! Event detail:")
            import json
            print(json.dumps(data, indent=2))
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_event_detail.py <event_id> [backend_url]")
        print("Example: python scripts/test_event_detail.py evt-283e6e7b")
        sys.exit(1)
    
    event_id = sys.argv[1]
    backend_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8000"
    
    test_event_detail(backend_url, event_id)
