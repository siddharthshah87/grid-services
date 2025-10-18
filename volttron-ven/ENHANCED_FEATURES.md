# Enhanced VEN Features

## Overview

The enhanced local VEN (`ven_local_enhanced.py`) adds three major capabilities:

1. **Device Shadow Sync** - AWS IoT Device Shadow integration
2. **Local Web UI** - Browser-based control panel  
3. **DR Event Handling** - Load curtailment with circuit-level control

## Quick Start

```bash
cd volttron-ven
./run_enhanced.sh
```

The VEN will start and display:
- MQTT connection status
- Web UI URL: `http://localhost:8080`

## 1. Device Shadow Sync

### What is Device Shadow?

AWS IoT Device Shadow is a cloud-based representation of your device state. It allows:
- Remote monitoring of VEN state
- Remote control of circuits (enable/disable)
- State persistence across reconnections
- Integration with other AWS services

### Shadow Document Structure

```json
{
  "state": {
    "reported": {
      "power_kw": 10.5,
      "shed_kw": 2.0,
      "base_power_kw": 12.5,
      "circuits": [
        {
          "id": "hvac1",
          "name": "HVAC",
          "enabled": true,
          "current_kw": 3.2,
          "critical": true
        },
        ...
      ],
      "active_event": {
        "event_id": "evt-123",
        "shed_kw": 2.0,
        "end_ts": 1234567890
      },
      "timestamp": 1234567890
    },
    "desired": {
      "circuits": [
        {
          "id": "hvac1",
          "enabled": false
        }
      ]
    }
  }
}
```

### Shadow Updates

- **Automatic**: Shadow updated every 30 seconds
- **On Events**: Shadow updated immediately when DR event starts/ends
- **On Changes**: Shadow updated when circuits are toggled

### View Shadow

```bash
# Get current shadow from AWS IoT
aws iot-data get-thing-shadow \
  --thing-name volttron_local_1234567890 \
  /tmp/shadow.json && cat /tmp/shadow.json | jq
```

### Update Shadow (Remote Control)

```bash
# Disable HVAC remotely via shadow
aws iot-data update-thing-shadow \
  --thing-name volttron_local_1234567890 \
  --payload '{"state":{"desired":{"circuits":[{"id":"hvac1","enabled":false}]}}}' \
  /tmp/shadow-update.json
```

The VEN will receive the delta and automatically disable the HVAC circuit.

## 2. Local Web UI

### Accessing the UI

Once the VEN is running, open your browser to:
```
http://localhost:8080
```

**Note for Codespaces**: Use port forwarding to access the UI:
1. In VS Code, go to the "PORTS" tab
2. Port 8080 should be auto-forwarded
3. Click the globe icon to open in browser
4. Or click "Forward Port" if it's not listed

### UI Features

#### Power Status Card
- **Connection Status**: Real-time MQTT connection indicator
- **Current Power**: Actual power consumption after curtailment
- **Load Shed**: Amount of power being curtailed
- **Base Power**: Normal power consumption without curtailment

#### DR Event Control Card
- **Trigger Event**: Manually start a DR event
  - Set shed amount (kW)
  - Set duration (seconds)
- **Active Event Display**: Shows event ID, shed amount, time remaining
- **Restore Button**: End event early and restore normal operation

#### Circuits Panel
- **Toggle Circuits**: Enable/disable individual circuits
- **Real-time Power**: See current power for each circuit
- **Critical Indicators**: Visual indicator for critical loads
- **Power Ratings**: Shows current vs rated power

### UI Auto-Refresh

The UI automatically refreshes every 2 seconds, showing:
- Latest power readings
- Circuit states
- Event status
- Connection status

## 3. DR Event Handling

### Load Curtailment Strategy

When a DR event is received, the VEN applies intelligent load curtailment:

#### Priority Order (Non-Critical First)
1. **Heater** (100% shed) - Can be fully disabled
2. **Lights** (70% shed) - Can be dimmed significantly
3. **House Load** (60% shed) - Miscellaneous loads
4. **EV Charger** (100% shed) - Can be paused
5. **HVAC** (20% shed) - Critical, keep 80% minimum
6. **Fridge** (20% shed) - Critical, keep 80% minimum

### Event Lifecycle

1. **Event Received** (via MQTT or UI)
   - Requested shed amount (e.g., 2.0 kW)
   - Duration (e.g., 300 seconds)
   
2. **Curtailment Applied**
   - Circuits shed according to priority
   - Actual shed amount calculated
   - Acknowledgment sent

3. **Active Event**
   - Telemetry shows reduced power
   - Shadow updated with event details
   - UI shows event status

4. **Event Ends**
   - Automatic: When duration expires
   - Manual: Via restore command or UI button
   - Circuits restored to normal operation

### Example: 2 kW Curtailment

Base power: 10.0 kW
Requested shed: 2.0 kW
Target power: 8.0 kW

**Shedding sequence:**
```
Heater:     1.5 kW → 0.0 kW  (shed 1.5 kW) 
Lights:     0.4 kW → 0.12 kW (shed 0.28 kW)
House Load: 1.0 kW → 0.78 kW (shed 0.22 kW)
Total shed: 2.0 kW ✅

HVAC:       3.5 kW (no change, critical)
Fridge:     0.2 kW (no change, critical)
EV:         0.0 kW (already off)
```

## Testing the Enhanced VEN

### 1. Start the VEN

```bash
./run_enhanced.sh
```

### 2. Open Web UI

Forward port 8080 in Codespaces, then open browser

### 3. Monitor Telemetry

In another terminal:
```bash
python3 ../scripts/ven_telemetry_listen.py \
  --ven-id volttron_local_<timestamp> \
  --endpoint a1mgxpe8mg484j-ats.iot.us-west-2.amazonaws.com
```

### 4. Trigger DR Event via UI

1. Set shed amount: 2.0 kW
2. Set duration: 300 seconds
3. Click "Trigger DR Event"
4. Watch power drop in telemetry
5. See circuits adjust in UI

### 5. Trigger DR Event via MQTT

```bash
python3 ../scripts/ven_cmd_publish.py \
  --op event \
  --ven-id volttron_local_<timestamp> \
  --endpoint a1mgxpe8mg484j-ats.iot.us-west-2.amazonaws.com \
  --shed-kw 2.5 \
  --duration-sec 600 \
  --corr-id test-event-001
```

### 6. Check Shadow

```bash
aws iot-data get-thing-shadow \
  --thing-name volttron_local_<timestamp> \
  /tmp/shadow.json && cat /tmp/shadow.json | jq '.state.reported'
```

### 7. Remote Circuit Control

```bash
# Disable EV charger remotely
aws iot-data update-thing-shadow \
  --thing-name volttron_local_<timestamp> \
  --payload '{"state":{"desired":{"circuits":[{"id":"ev1","enabled":false}]}}}' \
  /tmp/shadow-update.json
```

### 8. Restore Normal Operation

Via UI: Click "Restore Normal" button

Via MQTT:
```bash
python3 ../scripts/ven_cmd_publish.py \
  --op restore \
  --ven-id volttron_local_<timestamp> \
  --endpoint a1mgxpe8mg484j-ats.iot.us-west-2.amazonaws.com \
  --corr-id test-restore-001
```

## Architecture

### Components

1. **MQTT Thread** (`mqtt_client.loop_start()`)
   - Handles MQTT messages
   - Publishes telemetry every 5 seconds
   - Subscribes to commands and shadow delta

2. **Web Server Thread** (`Flask`)
   - Serves web UI on port 8080
   - Provides REST API for UI
   - Runs independently from MQTT

3. **Telemetry Loop** (`telemetry_loop()`)
   - Simulates base power changes
   - Calculates circuit power distribution
   - Publishes telemetry
   - Checks for expired events

4. **State Management** (`state_lock`)
   - Thread-safe state access
   - Shared between MQTT and web threads
   - Prevents race conditions

### Data Flow

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Backend   │◄───────►│  MQTT/IoT   │◄───────►│     VEN     │
│  (Commands) │         │    Core     │         │  (Enhanced) │
└─────────────┘         └─────────────┘         └──────┬──────┘
                              ▲                         │
                              │                         │
                              ▼                         │
                        ┌─────────────┐                 │
                        │   Device    │                 │
                        │   Shadow    │                 │
                        └─────────────┘                 │
                                                        │
                                                        ▼
                                                  ┌──────────┐
                                                  │  Web UI  │
                                                  │ :8080    │
                                                  └──────────┘
```

## Comparison: Basic vs Enhanced

| Feature | Basic VEN | Enhanced VEN |
|---------|-----------|--------------|
| MQTT Connection | ✅ | ✅ |
| Telemetry Publishing | ✅ | ✅ |
| Ping Command | ✅ | ✅ |
| Device Shadow | ❌ | ✅ |
| Web UI | ❌ | ✅ |
| DR Event Handling | ❌ | ✅ |
| Load Curtailment | ❌ | ✅ |
| Circuit Control | ❌ | ✅ |
| Remote Control | ❌ | ✅ |
| File Size | 173 lines | ~900 lines |

## Troubleshooting

### Port 8080 in Use

```bash
# Check what's using port 8080
lsof -i :8080

# Kill the process
kill -9 <PID>

# Or use a different port
export WEB_PORT=8081
./run_enhanced.sh
```

### Shadow Not Updating

```bash
# Check IoT policy allows shadow updates
aws iot get-policy --policy-name dev-volttron-policy | jq '.policyDocument'

# Should include:
# iot:UpdateThingShadow
# iot:GetThingShadow  
# iot:DeleteThingShadow
```

### Web UI Not Accessible in Codespaces

1. Open "PORTS" tab in VS Code
2. Find port 8080
3. Right-click → "Port Visibility" → "Public"
4. Click the globe icon to open

### Event Not Triggering

Check:
1. VEN is connected (see UI connection status)
2. Command format is correct (see examples above)
3. Check VEN logs for error messages
4. Verify MQTT client has permission to subscribe

## Next Steps

1. ✅ Test enhanced VEN locally
2. ✅ Verify shadow updates
3. ✅ Test DR events via UI and MQTT
4. 🔄 Integrate with backend API
5. 🔄 Add event scheduling
6. 🔄 Add historical data visualization
