# Running VEN Locally

## Overview

The VEN (Virtual End Node) is now designed to run locally instead of in the cloud. This approach provides:

- **Cost Savings**: No ECS tasks running 24/7
- **Stability**: No rc=7 MQTT disconnects from duplicate client IDs during rolling deployments
- **Easier Debugging**: Direct access to logs and faster iteration
- **Simplicity**: No health check endpoints or ALB required

## Prerequisites

1. AWS credentials configured (for IoT Core access and certificate retrieval)
2. Python 3 with `paho-mqtt` installed:
   ```bash
   pip install paho-mqtt
   ```

## Quick Start

### Minimal VEN (Recommended for Testing)

The minimal VEN (`ven_minimal.py`) is a stripped-down implementation that focuses on core MQTT functionality:

```bash
cd /workspaces/grid-services/volttron-ven
./run_minimal.sh
```

This will:
1. Fetch TLS certificates from AWS Secrets Manager (if not already cached)
2. Generate a unique client ID using timestamp
3. Connect to AWS IoT Core
4. Subscribe to command topic: `ven/cmd/{CLIENT_ID}`
5. Publish telemetry every 5 seconds to: `ven/telemetry/{CLIENT_ID}`

### Full VEN (Production)

The full VEN (`ven_agent.py`) includes additional features like shadow sync and health checks:

```bash
cd /workspaces/grid-services/volttron-ven
./run_local.sh
```

## Verifying Operation

### 1. Check VEN Logs

When running with `run_minimal.sh`, you'll see:
```
✅ Connected to AWS IoT Core (client_id=volttron_minimal_1234567890)
📡 Subscribing to command topic: ven/cmd/volttron_minimal_1234567890
✅ Connection established!
📊 Publishing telemetry every 5 seconds...
✓ [1] Published: 9.74 kW (connected=True)
✓ [2] Published: 10.79 kW (connected=True)
```

### 2. Monitor Telemetry Topic

In a separate terminal, subscribe to telemetry messages:

```bash
python3 scripts/ven_telemetry_listen.py \
  --ven-id volttron_minimal_1234567890 \
  --endpoint a1mgxpe8mg484j-ats.iot.us-west-2.amazonaws.com
```

Expected output:
```json
{
  "venId": "volttron_minimal_1234567890",
  "ts": 1760722235,
  "power_kw": 10.25,
  "shed_kw": 0.0,
  "message_num": 18
}
```

### 3. Send Commands

Send a ping command:
```bash
python3 scripts/ven_cmd_publish.py \
  --op ping \
  --ven-id volttron_minimal_1234567890 \
  --corr-id test-001
```

Monitor acknowledgments:
```bash
python3 scripts/ven_acks_listen.py \
  --ven-id volttron_minimal_1234567890 \
  --endpoint a1mgxpe8mg484j-ats.iot.us-west-2.amazonaws.com
```

## TLS Certificates

Certificates are cached locally in `./certs/` directory:
- `ca.pem` - AWS IoT Root CA
- `client.crt` - Client certificate
- `client.key` - Private key

These are automatically fetched from AWS Secrets Manager (`dev-volttron-tls`) on first run.

## Architecture

### MQTT Topics

- **Commands**: `ven/cmd/{venId}` - Backend → VEN
- **Acknowledgments**: `ven/ack/{venId}` - VEN → Backend
- **Telemetry**: `ven/telemetry/{venId}` - VEN → Backend

### Command Types

The minimal VEN currently supports:
- `ping` - Health check command

The full VEN additionally supports:
- `get` - Retrieve device state
- `set` - Update device state
- `enable`/`disable` - Enable/disable VEN
- `shedload` - Immediate load shedding
- `event` - DR event with duration and shed_kw

## Troubleshooting

### RC=7 Disconnects

If you see `MQTT disconnected: unexpected (code 7)`:
- This indicates a duplicate client ID
- Ensure no other VEN is running with the same client ID
- The minimal VEN uses timestamp-based unique IDs to avoid this

### Connection Timeout

If connection times out:
- Check AWS credentials: `aws sts get-caller-identity`
- Verify IoT endpoint: should be `a1mgxpe8mg484j-ats.iot.us-west-2.amazonaws.com`
- Check certificates exist in `./certs/`

### No Telemetry Messages

If VEN connects but doesn't publish:
- Check VEN logs for errors
- Verify connected=True in log messages
- Use `ven_telemetry_listen.py` to confirm messages reach AWS IoT Core

## Cloud Infrastructure (Removed)

The cloud VEN infrastructure has been removed to save costs and simplify operations:
- ~~ECS Service: `volttron-ven`~~
- ~~ALB: `volttron-alb`~~
- ~~Health checks~~

The local VEN connects directly to AWS IoT Core using mutual TLS authentication.

## Next Steps

1. Test command reception with ping
2. Add DR event handling to minimal VEN
3. Test full DR event flow (event → load shed → telemetry → backend logging)
