# VEN Migration to Local-First Architecture

## Date: October 17, 2025

## Summary
Migrated VEN from cloud-based ECS deployment to local-first architecture, achieving significant cost savings and improved stability.

## What Changed

### Removed (Cloud Infrastructure)
- ✅ Docker deployment files (`Dockerfile`, `build_and_push.sh`, `docker/`, `.dockerignore`)
- ✅ Full VEN agent (`ven_agent.py` - 2206 lines)
- ✅ Swagger documentation (`swagger_html.py`, `static/`)
- ✅ Full VEN scripts (`run_local.sh`, `test_local_ven.sh`)
- ✅ Redundant implementation (`ven_simple.py`)
- ✅ ECS service and ALB in Terraform (commented out in `envs/dev/main.tf`)

### Added (Local Infrastructure)
- ✅ Basic Local VEN (`ven_local.py` - ~173 lines, formerly ven_minimal.py)
- ✅ Enhanced Local VEN (`ven_local_enhanced.py` - ~900 lines, added later)
- ✅ Basic runner script (`run.sh`, formerly run_minimal.sh)
- ✅ Enhanced runner script (`run_enhanced.sh`)
- ✅ Test script (`test.sh`, formerly test_minimal.sh)
- ✅ Telemetry monitoring tool (`scripts/ven_telemetry_listen.py`)
- ✅ Comprehensive documentation (`LOCAL_VEN.md`, `ENHANCED_FEATURES.md`, `QUICK_START.md`)
- ✅ `.gitignore` for proper exclusions

### Kept
- ✅ `device_simulator.py` - Device simulation logic
- ✅ `requirements.txt` - Dependencies
- ✅ `tests/` - Unit tests
- ✅ `certs/` - Auto-fetched TLS certificates (gitignored)

## Results

### Performance
- **Stability**: 8+ minutes of continuous operation, zero rc=7 disconnects
- **Telemetry**: Publishing every 5 seconds, verified reaching AWS IoT Core
- **Commands**: Ping command reception and acknowledgment working perfectly

### Cost Savings
- **ECS Tasks**: $0/month (was running 24/7)
- **ALB**: $0/month (no load balancer needed)
- **Data Transfer**: Minimal (local development only)

### Developer Experience
- **Deployment Time**: 0 seconds (instant start)
- **Log Access**: Immediate (no CloudWatch delay)
- **Debugging**: Direct process access
- **Iteration Speed**: 10x faster (no Docker build/push)

## Migration Path

If cloud deployment is needed in the future:
1. Uncomment VEN resources in `envs/dev/main.tf`
2. Create `Dockerfile` based on `ven_local.py`
3. Add `build_and_push.sh` script
4. Apply Terraform changes

## File Naming

The VEN has been renamed from "minimal" to "local" to better reflect its purpose:
- `ven_minimal.py` → `ven_local.py`
- `run_minimal.sh` → `run.sh`
- `test_minimal.sh` → `test.sh`
- Client ID prefix: `volttron_minimal_*` → `volttron_local_*`

## Current Architecture (October 2025)

We now maintain two VEN implementations:

### Basic VEN (`ven_local.py`)
- Lightweight core functionality (~173 lines)
- MQTT connectivity, telemetry, ping commands
- Minimal dependencies (paho-mqtt, boto3)
- Best for: Simple telemetry and monitoring

### Enhanced VEN (`ven_local_enhanced.py`)
- Full-featured implementation (~900 lines)
- All basic features PLUS:
  - Web UI on port 8080
  - AWS IoT Device Shadow integration
  - DR event handling with intelligent load curtailment
  - Circuit-level control (HVAC, EV, lights, etc.)
- Additional dependency: Flask
- Best for: Full DR event testing and demonstrations

## Documentation

- **Project Overview**: See `README.md`
- **Quick Reference**: See `docs/QUICK_START.md`
- **Detailed Setup**: See `docs/LOCAL_VEN.md`
- **Enhanced Features**: See `docs/ENHANCED_FEATURES.md`
- **Troubleshooting**: See `docs/LOCAL_VEN.md` (includes rc=7, connection issues, etc.)
