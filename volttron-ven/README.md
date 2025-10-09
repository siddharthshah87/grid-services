# Volttron VEN Agent

## Overview
This agent implements a Virtual End Node (VEN) for grid event communication, designed to interact with OpenADR and Volttron platforms. It supports MQTT and HTTP protocols for event handling and reporting.

## Directory Structure
- `ven_agent.py`: Main agent logic
- `requirements.txt`: Python dependencies
- `Dockerfile`, `build_and_push.sh`: Containerization and build scripts
- `static/`, `docker/`, `tests/`: Static files, Docker resources, and tests

## Setup
### Prerequisites
- Python 3.8+
- pip
- Docker (optional)

### Installation
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the Agent
```bash
python ven_agent.py
```
Or with Docker:
```bash
docker build -t volttron-ven .
docker run --rm volttron-ven
```

## Configuration
- Environment variables can be set for MQTT/HTTP endpoints, credentials, and logging.
- See comments in `ven_agent.py` for configurable options.

## API / Message Formats
- **MQTT Topics:**
  - `ven/events`: Receives grid events
  - `ven/acks`: Publishes acknowledgments
- **HTTP Endpoints:**
  - `/event`: Receives event POSTs
  - `/ack`: Sends acknowledgment
- Message format: JSON objects with event metadata, timestamps, and status.

## Testing

### Test Coverage
Unit tests are provided in `tests/test_ven_agent.py` and cover:
- Event handling and MQTT publish logic
- Main loop and shadow sync
- Health endpoint and OpenAPI spec
- TLS hostname verification logic

To run all tests:
```bash
pytest tests/
```

Tests use Python's `unittest.mock` for MQTT and environment simulation. Add new tests for any new features or bug fixes.

## Contributing
- Add docstrings and comments to new code.
- Update this README with new features or configuration options.

## License
Specify license here.
