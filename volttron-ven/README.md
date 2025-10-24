# Volttron VEN Agent

## Overview
This is a **production-ready** Virtual End Node (VEN) for Demand Response (DR) event communication via MQTT. It connects to AWS IoT Core for command/control and telemetry publishing.

**💡 Quick Start:** See [docs/QUICK_START.md](docs/QUICK_START.md) for step-by-step instructions.

## Features
- ✅ Stable MQTT connectivity with AWS IoT Core and auto-reconnect
- ✅ Telemetry publishing every 5 seconds to shared topic (`volttron/metering`)
- ✅ DR event handling with priority-based load curtailment
- ✅ Web UI for real-time monitoring and control
- ✅ AWS IoT Device Shadow sync
- ✅ Persistent MQTT session (QoS1 messages queued during disconnects)
- ✅ Auto-fetches TLS certificates from AWS Secrets Manager
- ✅ Unified control script for all operations

## Quick Start

### Start VEN
```bash
./scripts/ven_control.sh start
```

### Send DR Event
```bash
./scripts/ven_control.sh send-event --shed-kw 2.0 --duration 300
```

### Check Status
```bash
./scripts/ven_control.sh status
```

### View Web UI
Open browser to: `http://localhost:8080`

**Full command reference:** [docs/VEN_OPERATIONS.md](docs/VEN_OPERATIONS.md)

## Directory Structure
- `ven_local_enhanced.py`: Production VEN with DR capabilities (~900 lines) ⭐
- `run_enhanced.sh`: VEN startup script (supports `--background`)
- `certs/`: TLS certificates (auto-fetched from AWS Secrets Manager)
- `docs/`: Documentation
  - `QUICK_START.md`: **Quick reference guide**
  - `ENHANCED_FEATURES.md`: Feature details and examples
  - `LOCAL_VEN.md`: Setup and troubleshooting
  - `CHANGES.md`: Migration history
- `hardware_interfaces/`: Hardware interface modules (GPIO, power meters)
- `requirements.txt`: Python dependencies

## Prerequisites
- Python 3.8+
- AWS credentials configured (IoT Core access)
- Dependencies: `paho-mqtt`, `boto3`, `flask`

## Configuration

The VEN uses consistent identity via `IOT_THING_NAME`:
- **Thing Name**: `volttron_thing` (matches pre-registered AWS IoT certificates)
- **Telemetry Topic**: `volttron/metering` (shared topic for all VENs)
- **Command Topic**: `ven/cmd/volttron_thing`
- **Certificates**: Fetched from AWS Secrets Manager (`dev-volttron-tls`)

## MQTT Topics

| Topic | Purpose | Direction |
|-------|---------|-----------|
| `volttron/metering` | Telemetry (shared by ALL VENs) | VEN → Backend |
| `ven/cmd/volttron_thing` | DR commands | Backend → VEN |
| `ven/ack/volttron_thing` | Command acknowledgments | VEN → Backend |
| `$aws/things/volttron_thing/shadow/...` | Device Shadow | Bidirectional |

## Testing

### End-to-End Flow
```bash
# 1. Start VEN
./scripts/ven_control.sh start

# 2. Send DR event
./scripts/ven_control.sh send-event --shed-kw 2.0 --duration 300

# 3. Verify load shedding
./scripts/ven_control.sh shadow

# 4. Restore loads
./scripts/ven_control.sh restore

# 5. Stop VEN
./scripts/ven_control.sh stop
```

### Circuit History API
Get historical power usage data for individual circuits/loads:

```bash
# Get last 10 circuit snapshots for volttron_thing
curl -s "http://backend-alb-948465488.us-west-2.elb.amazonaws.com/api/vens/volttron_thing/circuits/history?limit=10" | jq '.'

# Get specific circuit history
curl -s "http://backend-alb-948465488.us-west-2.elb.amazonaws.com/api/vens/volttron_thing/circuits/history?load_id=hvac1&limit=20" | jq '.'

# Get history within time range (ISO 8601 timestamps)
curl -s "http://backend-alb-948465488.us-west-2.elb.amazonaws.com/api/vens/volttron_thing/circuits/history?start=2025-10-23T00:00:00Z&end=2025-10-24T00:00:00Z" | jq '.'
```

**Response includes:**
- `timestamp`: When the snapshot was taken
- `loadId`: Circuit identifier (hvac1, heater1, ev1, etc.)
- `name`: Human-readable name
- `type`: Circuit type (hvac, heater, ev, etc.)
- `capacityKw`: Maximum circuit capacity
- `currentPowerKw`: Current power draw
- `shedCapabilityKw`: How much power can be shed (0 for critical loads)
- `enabled`: Whether circuit is enabled
- `priority`: Load priority (1=critical, 5=flexible)

**Expected Results:**
- VEN connects within 30 seconds
- Event command received within 2 seconds
- Loads curtailed achieving ~2 kW reduction
- Acknowledgment sent to backend
- Shadow shows active event and reduced power
- Telemetry includes event marker
- Restore command returns loads to normal
- Circuit history updated every 5 seconds

## Documentation

- **Quick Start**: [docs/QUICK_START.md](docs/QUICK_START.md) - Get running in 5 minutes
- **Operations Guide**: [/docs/VEN_OPERATIONS.md](/docs/VEN_OPERATIONS.md) - Complete reference
- **Enhanced Features**: [docs/ENHANCED_FEATURES.md](docs/ENHANCED_FEATURES.md) - Web UI, Shadow, DR events
- **Local VEN Guide**: [docs/LOCAL_VEN.md](docs/LOCAL_VEN.md) - Setup and troubleshooting

## Architecture

The VEN implements a scalable topic architecture:
- **Shared telemetry topic** (`volttron/metering`) used by ALL VENs with `venId` in payload
- **Per-VEN command topics** (`ven/cmd/{venId}`) for targeted command delivery
- **Single IoT Rule** forwards shared topic to backend (scales to 10,000+ VENs)

See [/docs/VEN_OPERATIONS.md](/docs/VEN_OPERATIONS.md#architecture-notes) for details.

## Validated Scenarios

✅ **MQTT Connectivity**
- TLS handshake with AWS IoT Core
- Persistent session with auto-reconnect
- QoS1 message delivery guarantees

✅ **DR Event Handling**
- Event command reception and parsing
- Priority-based load curtailment
- Baseline calculation for M&V
- Acknowledgment publishing
- Event duration tracking with auto-restore

✅ **Telemetry & Monitoring**
- Continuous telemetry publishing (5s intervals)
- Device Shadow synchronization
- Web UI real-time updates
- IoT Rule forwarding to backend

✅ **Load Curtailment**
- Non-critical loads shed first (heater, lights, EV)
- Critical loads reduced minimally (HVAC, fridge)
- Accurate power measurement and reporting
- Graceful restoration after event

## Support

For issues or questions:
1. Check [/docs/VEN_OPERATIONS.md](/docs/VEN_OPERATIONS.md#troubleshooting)
2. Review logs: `./scripts/ven_control.sh logs`
3. Verify AWS IoT connectivity: `aws iot describe-thing --thing-name volttron_thing`

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
- Run `./test.sh` to verify VEN functionality before committing
- Run `pytest` from project root to verify all tests pass
- Update docs/LOCAL_VEN.md for operational changes

