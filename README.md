## OpenADR VTN

The `openleadr/vtn_server.py` script provides a minimal VTN for testing. The
server listens on port `8080` for OpenADR traffic. It now tracks the VENs that
register with it and exposes a simple HTTP endpoint to list them.

### Listing active VENs

Run the server and then access `http://localhost:8081/vens` to retrieve a JSON
array of currently registered VEN IDs.
