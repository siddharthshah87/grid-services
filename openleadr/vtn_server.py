# openleadr/vtn_server.py
from openleadr import OpenADRServer

server = OpenADRServer(vtn_id="my-vtn", http_port=8080)

@server.add_handler("on_create_party_registration")
def handle_registration(registration_info):
    return {
        "ven_id": registration_info.get("ven_id", "ven123"),
        "registration_id": "reg123",
        "poll_interval": 10
    }

@server.add_handler("on_request_event")
def handle_event_request(ven_id, request):
    print(f"Request from {ven_id}: {request}")
    return []

server.run()
