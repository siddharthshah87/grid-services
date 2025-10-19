# VEN Operations Guide

## Quick Start

### Start VEN
```bash
./scripts/ven_control.sh start
```

The VEN will start in background mode with:
- **Thing Name**: `volttron_thing` (matches AWS IoT certificates)
- **Web UI**: http://localhost:8080
- **Logs**: `/tmp/ven_enhanced.log`

### Check Status
```bash
./scripts/ven_control.sh status
```

### Send DR Event
```bash
# Shed 2 kW for 5 minutes
./scripts/ven_control.sh send-event --shed-kw 2.0 --duration 300 --event-id evt-001
```

### Restore Loads
```bash
./scripts/ven_control.sh restore
```

### Stop VEN
```bash
./scripts/ven_control.sh stop
```

## VEN Configuration

### Thing Name & Certificates
The VEN **must** use `IOT_THING_NAME=volttron_thing` because:
- Certificates in `volttron-ven/certs/` are registered to AWS IoT thing `volttron_thing`
- Certificate ARN: `arn:aws:iot:us-west-2:923675928909:cert/478c55f3a33a019bef1e489312813ed6dc123720b759c378fa4f66a4f74ecad3`
- This ensures consistent identity across restarts

### MQTT Topics

| Topic | Purpose | Direction |
|-------|---------|-----------|
| `volttron/metering` | Telemetry (ALL VENs) | VEN → Backend |
| `ven/cmd/volttron_thing` | Commands | Backend → VEN |
| `ven/ack/volttron_thing` | Acknowledgments | VEN → Backend |
| `ven/telemetry/volttron_thing` | Debug telemetry | VEN → Monitoring |

**Key Design**: All VENs publish to shared `volttron/metering` topic with `venId` in payload. This scales efficiently - no per-VEN topics needed.

### Environment Variables

```bash
# Required
export IOT_THING_NAME=volttron_thing        # Must match certificate
export IOT_ENDPOINT=a1mgxpe8mg484j-ats.iot.us-west-2.amazonaws.com

# Optional
export BACKEND_URL=http://backend-alb-948465488.us-west-2.elb.amazonaws.com
export WEB_PORT=8080
```

## Backend Integration

### VEN Registration
VENs auto-register on first telemetry. Manual registration:

```bash
./scripts/ven_control.sh register
```

Or via API:
```bash
curl -X POST http://backend-alb-948465488.us-west-2.elb.amazonaws.com/api/vens/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "VEN volttron_thing",
    "status": "online",
    "location": {"lat": 37.7749, "lon": -122.4194},
    "registrationId": "volttron_thing"
  }'
```

### EventCommandService
Backend service automatically dispatches commands when events become active:

1. Monitors `events` table every 5 seconds
2. Finds events with status="active" and `startTime <= now <= endTime`
3. Queries VENs with status="online"
4. Publishes DR commands to `ven/cmd/{ven.registration_id}` via AWS IoT Core

**Important**: EventCommandService uses `ven.registration_id` field, not database `ven_id`.

## Command Structure

### DR Event Command
```json
{
  "op": "event",
  "correlationId": "corr-1234567890",
  "venId": "volttron_thing",
  "event_id": "evt-001",
  "shed_kw": 2.0,
  "duration_sec": 300
}
```

### Restore Command
```json
{
  "op": "restore",
  "correlationId": "restore-1234567890",
  "venId": "volttron_thing"
}
```

### VEN Acknowledgment
```json
{
  "op": "event",
  "status": "accepted",
  "event_id": "evt-001",
  "requested_shed_kw": 2.0,
  "actual_shed_kw": 1.8,
  "ts": 1760816635,
  "correlationId": "corr-1234567890"
}
```

## Monitoring

### View Logs
```bash
# Follow live logs
./scripts/ven_control.sh logs

# Or directly
tail -f /tmp/ven_enhanced.log
```

### Check IoT Shadow
```bash
./scripts/ven_control.sh shadow
```

Output:
```json
{
  "power_kw": 10.0,
  "shed_kw": 0.0,
  "active_event": null,
  "circuits": [
    {"name": "HVAC", "enabled": true, "current_kw": 5.5},
    {"name": "Heater", "enabled": true, "current_kw": 2.5},
    {"name": "EV Charger", "enabled": false, "current_kw": 0.0},
    ...
  ]
}
```

### Monitor Telemetry
```bash
./scripts/ven_control.sh telemetry
```

## Troubleshooting

### VEN Won't Connect to MQTT
**Symptom**: Log shows "⏳ Waiting for MQTT connection..." but never "✅ Connected"

**Possible Causes**:
1. Certificate mismatch - ensure `IOT_THING_NAME=volttron_thing`
2. Certificate expired - check AWS IoT Core certificate status
3. Network issue - verify IoT endpoint reachable
4. Thing doesn't exist - verify thing `volttron_thing` exists in AWS IoT

**Debug**:
```bash
# Check thing exists
aws iot describe-thing --thing-name volttron_thing

# Check certificates
aws iot list-thing-principals --thing-name volttron_thing

# Test connectivity
openssl s_client -connect a1mgxpe8mg484j-ats.iot.us-west-2.amazonaws.com:8883 \
  -CAfile volttron-ven/certs/ca.pem \
  -cert volttron-ven/certs/client.crt \
  -key volttron-ven/certs/client.key
```

### VEN Not Receiving Commands
**Symptom**: Commands published but VEN doesn't respond

**Check**:
1. VEN subscribed to correct topic: `ven/cmd/volttron_thing`
2. Backend publishing to correct topic (check `registration_id` field)
3. AWS IoT policy allows publish/subscribe

**Test manually**:
```bash
./scripts/ven_cmd_publish.py \
  --ven-id volttron_thing \
  --op event \
  --shed-kw 1.0 \
  --duration 180
```

### Telemetry Not Reaching Backend
**Symptom**: VEN running but backend shows no telemetry

**Check**:
1. VEN publishing to `volttron/metering` (shared topic)
2. IoT Rule `mqtt_forward_volttron_metering` exists and enabled
3. Kinesis stream receiving messages
4. Backend MQTT consumer running

**Verify**:
```bash
# Check IoT Rule
aws iot get-topic-rule --rule-name mqtt_forward_volttron_metering

# Check Kinesis
aws kinesis describe-stream --stream-name mqtt-forward-mqtt-stream

# Backend health
curl http://backend-alb-948465488.us-west-2.elb.amazonaws.com/health
```

## Architecture Notes

### Scalability
- **Shared telemetry topic**: All VENs publish to `volttron/metering`
- **Per-VEN commands**: Commands sent to `ven/cmd/{venId}` for security
- **VEN ID in payload**: Database uses `venId` field from telemetry JSON
- **Single IoT Rule**: One rule handles all VEN telemetry

This design scales from 1 to 10,000+ VENs without infrastructure changes.

### Load Shedding Strategy
1. VEN calculates baseline power (average of last 60 samples)
2. On DR event, targets: `current_power - shed_kw`
3. Disables non-critical circuits first (priority order)
4. Continues telemetry at reduced power
5. On restore, re-enables circuits

### Measurement & Verification (M&V)
- Baseline: 5-minute average before event
- Actual shed: `baseline_power - current_power`
- Reported in acknowledgment and shadow

## Files Reference

### Scripts
- `scripts/ven_control.sh` - Unified VEN control (start/stop/status/etc)
- `scripts/ven_cmd_publish.py` - Publish commands via AWS IoT
- `scripts/register_ven.py` - Register VEN in backend database
- `scripts/ven_telemetry_listen.py` - Monitor MQTT telemetry

### VEN Implementation
- `volttron-ven/ven_local_enhanced.py` - Main VEN with DR capabilities (~865 lines)
- `volttron-ven/run_enhanced.sh` - Startup script with proper configuration
- `volttron-ven/certs/` - AWS IoT certificates (ca.pem, client.crt, client.key)

### Backend Services
- `ecs-backend/app/services/event_command_service.py` - Automatic command dispatch
- `ecs-backend/app/services/mqtt_consumer.py` - Telemetry ingestion
- `ecs-backend/app/core/config.py` - Configuration including MQTT topics

## Quick Reference

```bash
# Complete workflow
./scripts/ven_control.sh start                    # Start VEN
./scripts/ven_control.sh status                   # Verify running
./scripts/ven_control.sh send-event \            # Trigger DR event
  --shed-kw 2.0 --duration 300
./scripts/ven_control.sh shadow                   # Check load shedding
./scripts/ven_control.sh restore                  # Restore loads
./scripts/ven_control.sh stop                     # Stop VEN
```
