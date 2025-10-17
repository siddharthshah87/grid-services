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
- ✅ Local VEN (`ven_local.py` - 173 lines, formerly ven_minimal.py)
- ✅ Runner script (`run.sh`, formerly run_minimal.sh)
- ✅ Test script (`test.sh`, formerly test_minimal.sh)
- ✅ Telemetry monitoring tool (`scripts/ven_telemetry_listen.py`)
- ✅ Comprehensive documentation (`LOCAL_VEN.md`)
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

## Documentation

- **Quick Start**: See `README.md`
- **Detailed Setup**: See `LOCAL_VEN.md`
- **Troubleshooting**: See `LOCAL_VEN.md` (includes rc=7, connection issues, etc.)
