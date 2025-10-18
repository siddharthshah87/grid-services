# Volttron VEN Agent

## Overview
This is a **local-first** Virtual End Node (VEN) for Demand Response (DR) event communication via MQTT. It connects to AWS IoT Core for command/control and telemetry publishing.

**💡 Quick Start:** See [LOCAL_VEN.md](docs/LOCAL_VEN.md) for detailed setup instructions.

## Features
- ✅ Stable MQTT connectivity with AWS IoT Core (zero rc=7 disconnects)
- ✅ Telemetry publishing every 5 seconds
- ✅ Command reception (ping, events)
- ✅ Lightweight and maintainable (173 lines)
- ✅ Auto-fetches TLS certificates from AWS Secrets Manager
- ✅ Cost-effective (no cloud infrastructure needed)

## Quick Start

### Basic VEN
```bash
cd volttron-ven
./run.sh
```

### Enhanced VEN (with Web UI + Shadow + DR Events)
```bash
cd volttron-ven
./run_enhanced.sh
# Open browser to http://localhost:8080
```

See [ENHANCED_FEATURES.md](docs/ENHANCED_FEATURES.md) for details on advanced capabilities.

## Directory Structure
- `ven_local.py`: Basic VEN implementation (~173 lines) ⭐
- `ven_local_enhanced.py`: Enhanced VEN with Web UI and DR events (~900 lines)
- `run.sh`: Basic VEN runner script with cert setup
- `run_enhanced.sh`: Enhanced VEN runner script
- `test.sh`: Automated test script
- `docs/`: Documentation folder
  - `LOCAL_VEN.md`: **Comprehensive setup & troubleshooting guide**
  - `ENHANCED_FEATURES.md`: Enhanced VEN feature details
  - `QUICK_START.md`: Quick reference guide
  - `CHANGES.md`: Migration history and rationale
- `requirements.txt`: Python dependencies (paho-mqtt, boto3)
- `device_simulator.py`: Device simulation logic (for future use)
- `certs/`: TLS certificates (auto-fetched, gitignored)


## Prerequisites
- Python 3.8+
- AWS credentials configured (for IoT Core access and cert fetching)
- Dependencies: `pip install paho-mqtt boto3`

## Installation

No installation needed! Just run the script:
```bash
./run.sh
```

The script will:
1. Check for TLS certificates in `./certs/`
2. Fetch them from AWS Secrets Manager if missing
3. Start the VEN with a unique client ID

## Configuration

The VEN connects to AWS IoT Core using mutual TLS. Environment variables:
Or with Docker:
```bash
docker build -t volttron-ven .
docker run --rm volttron-ven
```

## Configuration
- Environment variables can be set for MQTT/HTTP endpoints, credentials, and logging.
- See comments in `ven_agent.py` for configurable options.


- `IOT_ENDPOINT`: AWS IoT Core endpoint (e.g., `a1mgxpe8mg484j-ats.iot.us-west-2.amazonaws.com`)
- `CLIENT_ID`: Unique MQTT client ID (auto-generated with timestamp in run.sh)
- Certificate paths are auto-configured (fetched from AWS Secrets Manager)

## MQTT Topics

- **Commands** (Backend → VEN): `ven/cmd/{venId}`
- **Acknowledgments** (VEN → Backend): `ven/ack/{venId}`
- **Telemetry** (VEN → Backend): `ven/telemetry/{venId}`

## Testing

### Automated Test Script

Run the automated test script to verify VEN operation:
```bash
./test.sh
```

### Manual Verification

```bash
# 1. Run local VEN
./run.sh

# 2. In another terminal, monitor telemetry
python3 ../scripts/ven_telemetry_listen.py \
  --ven-id <your-client-id> \
  --endpoint a1mgxpe8mg484j-ats.iot.us-west-2.amazonaws.com

# 3. Send a ping command
python3 ../scripts/ven_cmd_publish.py \
  --op ping \
  --ven-id <your-client-id> \
  --endpoint a1mgxpe8mg484j-ats.iot.us-west-2.amazonaws.com \
  --corr-id test-001
```

See [docs/QUICK_START.md](docs/QUICK_START.md) for more testing examples.

## Architecture

### Local VEN Benefits
- ✅ **Cost Savings**: No ECS tasks or ALB running 24/7
- ✅ **Stability**: Eliminates rc=7 MQTT disconnects from rolling deployments
- ✅ **Debugging**: Direct log access, faster iteration
- ✅ **Simplicity**: No health checks or cloud complexity needed

### Message Flow
```
Backend → ven/cmd/{venId} → VEN processes command
VEN → ven/ack/{venId} → Backend receives acknowledgment
VEN → ven/telemetry/{venId} → Backend receives telemetry (every 5s)
```

## Troubleshooting

See [LOCAL_VEN.md](docs/LOCAL_VEN.md) for detailed troubleshooting, including:
- RC=7 disconnect issues
- Connection timeouts  
- Certificate problems
- Missing telemetry

## Contributing
- Add docstrings and comments to new code
- Update documentation for new features
- Run `./test.sh` to verify functionality before committing
- Update docs/LOCAL_VEN.md for operational changes

