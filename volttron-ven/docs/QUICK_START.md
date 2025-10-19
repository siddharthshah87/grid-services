# VEN Quick Start

## 🚀 Run the Enhanced VEN (Recommended)

**Use the unified control script for all VEN operations:**

```bash
# Start VEN in background
./scripts/ven_control.sh start

# Check status
./scripts/ven_control.sh status

# View logs
./scripts/ven_control.sh logs
```

### What You Get

**File**: `ven_local_enhanced.py` (~900 lines)

**Features**:
- ✅ MQTT connection to AWS IoT Core with auto-reconnect
- 🌐 Web UI at `http://localhost:8080`
- 📱 AWS IoT Device Shadow sync
- ⚡ DR event handling with intelligent load curtailment
- 🎛️ Circuit-level control (HVAC, EV, lights, etc.)
- 🔄 Remote control via shadow updates
- 📊 Telemetry publishing every 5 seconds
- ⚙️ Persistent session (messages queued during disconnects)

### Configuration

The VEN runs with:
- **Thing Name**: `volttron_thing` (matches AWS IoT certificates)
- **Telemetry Topic**: `volttron/metering` (shared topic for all VENs)
- **Command Topic**: `ven/cmd/volttron_thing`
- **Web UI Port**: 8080

**Important**: Thing name is fixed to `volttron_thing` because certificates are pre-registered to this AWS IoT Thing.

## 🧪 Test DR Event Flow

### Send Event Command
```bash
# Shed 2 kW for 5 minutes
./scripts/ven_control.sh send-event --shed-kw 2.0 --duration 300 --event-id evt-test-001
```

**Expected**:
- VEN receives command within 2 seconds
- Loads are curtailed (heater, lights reduced first)
- Power drops by ~2 kW
- Acknowledgment sent to `ven/ack/volttron_thing`
- Shadow updated with active event

### Monitor Results
```bash
# View VEN logs
./scripts/ven_control.sh logs

# Check IoT Shadow
./scripts/ven_control.sh shadow

# Monitor telemetry
./scripts/ven_control.sh telemetry
```

### Restore Loads
```bash
./scripts/ven_control.sh restore
```

## 🛑 Stop the VEN

```bash
./scripts/ven_control.sh stop
```

## 📁 Key Files

- `ven_local_enhanced.py` - Enhanced VEN with UI and DR (~900 lines)
- `run_enhanced.sh` - VEN startup script (supports `--background`)
- `certs/` - AWS IoT certificates (auto-downloaded from Secrets Manager)
- `../scripts/ven_control.sh` - Unified control script (start/stop/status/events)

## 📚 More Info

- **Detailed Features**: [ENHANCED_FEATURES.md](ENHANCED_FEATURES.md)
- **Operations Guide**: [/docs/VEN_OPERATIONS.md](/docs/VEN_OPERATIONS.md)
- **Project Overview**: [../README.md](../README.md)

## ✅ Validated E2E Flow

The VEN has been tested end-to-end:
- ✅ MQTT connection with persistent session
- ✅ Telemetry publishing to shared `volttron/metering` topic
- ✅ DR event command reception and acknowledgment
- ✅ Load curtailment (priority-based circuit shedding)
- ✅ Device Shadow updates during events
- ✅ Restore command and load recovery
- ✅ Web UI real-time state display
