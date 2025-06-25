# openleadr/vtn_server.py
"""Simple VTN server example used for development.

This file now keeps track of all VENs that register with the VTN and exposes
an additional HTTP endpoint on port 8081 that lists those active VENs.
"""

from openleadr import OpenADRServer
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import threading

active_vens = set()

server = OpenADRServer(vtn_id="my-vtn", http_port=8080)

@server.add_handler("on_create_party_registration")
def handle_registration(registration_info):
    ven_id = registration_info.get("ven_id", "ven123")
    active_vens.add(ven_id)
    print(f"VEN registered: {ven_id}")
    return {
        "ven_id": ven_id,
        "registration_id": "reg123",
        "poll_interval": 10
    }

@server.add_handler("on_cancel_party_registration")
def handle_cancel_registration(ven_id, registration_id):
    active_vens.discard(ven_id)
    print(f"VEN unregistered: {ven_id}")
    return True

@server.add_handler("on_request_event")
def handle_event_request(ven_id, request):
    print(f"Request from {ven_id}: {request}")
    return []

class VensHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/vens":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            payload = json.dumps(sorted(list(active_vens))).encode()
            self.wfile.write(payload)
        else:
            self.send_response(404)
            self.end_headers()


def run_vens_server():
    httpd = HTTPServer(("0.0.0.0", 8081), VensHandler)
    httpd.serve_forever()


if __name__ == "__main__":
    thread = threading.Thread(target=run_vens_server, daemon=True)
    thread.start()
    server.run()
