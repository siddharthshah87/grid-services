# VEN Quick Start

## 🚀 Run the VEN

We have two VEN implementations to choose from:

### Basic VEN - Lightweight & Simple

**File**: `ven_local.py` (~173 lines)
**Run**: `./run.sh`

```bash
cd volttron-ven
./run.sh
```

**Features**:
- ✅ MQTT connection to AWS IoT Core
- ✅ Telemetry publishing (every 5s)
- ✅ Ping command handling
- ✅ Minimal resource usage

**Best for**: Simple telemetry and monitoring

### Enhanced VEN - Full Featured ⭐

**File**: `ven_local_enhanced.py` (~900 lines)
**Run**: `./run_enhanced.sh`

```bash
cd volttron-ven
./run_enhanced.sh
```

**Features**: Everything in Basic PLUS:
- 🌐 Web UI at `http://localhost:8080`
- 📱 AWS IoT Device Shadow sync
- ⚡ DR event handling with intelligent load curtailment
- 🎛️ Circuit-level control (HVAC, EV, lights, etc.)
- 🔄 Remote control via shadow updates

**Best for**: Full DR event testing and demonstrations

### Both Versions Include

- Auto-fetch TLS certificates from AWS Secrets Manager
- Connect to AWS IoT Core with unique timestamp-based client ID
- Publish telemetry every 5 seconds
- Handle MQTT reconnections gracefully

## 📊 Monitor Telemetry

In another terminal:
```bash
# Get the client ID from VEN output, then:
python3 ../scripts/ven_telemetry_listen.py \
  --ven-id volttron_local_<timestamp> \
  --endpoint a1mgxpe8mg484j-ats.iot.us-west-2.amazonaws.com
```

## 🧪 Test Commands

```bash
# Send ping
python3 ../scripts/ven_cmd_publish.py \
  --op ping \
  --ven-id volttron_local_<timestamp> \
  --endpoint a1mgxpe8mg484j-ats.iot.us-west-2.amazonaws.com \
  --corr-id test-001

# Monitor acks
python3 ../scripts/ven_acks_listen.py \
  --ven-id volttron_local_<timestamp> \
  --endpoint a1mgxpe8mg484j-ats.iot.us-west-2.amazonaws.com
```

## 🛑 Stop the VEN

Press `Ctrl+C` in the VEN terminal

## 📁 Key Files

- `ven_local.py` - Basic VEN implementation (~173 lines)
- `ven_local_enhanced.py` - Enhanced VEN with UI and DR (~900 lines)
- `run.sh` - Basic VEN runner with cert setup
- `run_enhanced.sh` - Enhanced VEN runner with Flask install
- `test.sh` - Automated test script
- `device_simulator.py` - Device simulation logic

## 📚 More Info

- **Detailed Setup & Troubleshooting**: [LOCAL_VEN.md](LOCAL_VEN.md)
- **Enhanced Features Guide**: [ENHANCED_FEATURES.md](ENHANCED_FEATURES.md)
- **Project Overview**: [../README.md](../README.md)
- **Migration History**: [CHANGES.md](CHANGES.md)

## ✅ Status

**Basic VEN**:
- ✅ Stable MQTT connection (zero rc=7 disconnects)
- ✅ Telemetry publishing (every 5s)
- ✅ Ping command handling

**Enhanced VEN**:
- ✅ All basic VEN features
- ✅ Web UI on port 8080
- ✅ DR event handling with load curtailment
- ✅ Device Shadow sync
- ✅ Circuit-level control
