# VEN Quick Start

## 🚀 Run the VEN

```bash
cd volttron-ven
./run.sh
```

That's it! The VEN will:
- Auto-fetch TLS certificates from AWS Secrets Manager
- Connect to AWS IoT Core with unique client ID
- Start publishing telemetry every 5 seconds

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

- `ven_local.py` - Main VEN implementation (173 lines)
- `run.sh` - Runner with cert setup
- `test.sh` - Automated test
- `device_simulator.py` - Device logic (for future use)

## 📚 More Info

- **Detailed Setup**: See [LOCAL_VEN.md](LOCAL_VEN.md)
- **Architecture**: See [README.md](README.md)
- **Migration History**: See [CHANGES.md](CHANGES.md)

## ✅ Status

- ✅ Stable MQTT connection (8+ min, zero rc=7 disconnects)
- ✅ Telemetry publishing (every 5s)
- ✅ Command reception (ping verified)
- ✅ Message delivery to AWS IoT Core confirmed
- 🔄 DR event handling (in progress)
