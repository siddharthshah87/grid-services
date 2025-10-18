# VEN Implementation Testing Plan

## Overview
This document outlines the complete plan to implement, test, and validate the VEN (Virtual End Node) system that works end-to-end with the backend API for demand response events.

**Current Branch**: `ven-local-complete`  
**Goal**: Complete event creation → backend command dispatch → VEN load shedding → telemetry/ack response flow

---

## Current State Assessment

### ✅ What's Working
1. **VEN Implementation** (`volttron-ven/`)
   - ✅ Basic VEN (`ven_local.py`) - MQTT connectivity, telemetry publishing
   - ✅ Enhanced VEN (`ven_local_enhanced.py`) - Web UI, Shadow sync, DR events
   - ✅ MQTT connection to AWS IoT Core with TLS
   - ✅ Command reception on `ven/cmd/{venId}`
   - ✅ Acknowledgment publishing on `ven/ack/{venId}`
   - ✅ Telemetry publishing on `ven/telemetry/{venId}` and `oadr/meter/{venId}`

2. **Backend API** (`ecs-backend/`)
   - ✅ VEN registration API (`POST /api/vens/`)
   - ✅ Event creation API (`POST /api/events/`)
   - ✅ MQTT consumer for telemetry (`mqtt_consumer.py`)
   - ✅ Database models for VENs, Events, Telemetry
   - ✅ Telemetry persistence and aggregation

3. **Scripts** (`scripts/`)
   - ✅ `register_ven.py` - Register VEN in backend
   - ✅ `send_event.py` - Publish test event
   - ✅ `monitor_ven.py` - Listen to VEN responses
   - ✅ `ven_cmd_publish.py` - Send commands to VEN
   - ✅ `ven_acks_listen.py` - Listen to VEN acknowledgments
   - ✅ `ven_telemetry_listen.py` - Monitor VEN telemetry

### ❌ What's Missing
1. **Backend Event-to-Command Service**
   - Backend does NOT automatically send commands to VENs when events are created/started
   - Need service to monitor events and dispatch `shedPanel` or `event` commands via MQTT
   - Should handle event lifecycle: start, progress monitoring, stop/cancel

2. **VEN Load Shedding Enhancement**
   - Current VEN has basic load shedding but needs refinement
   - Priority-based load curtailment algorithm needs improvement
   - Baseline calculation for M&V (Measurement & Verification)
   - Better handling of temporary vs. permanent load limits

3. **Integration Testing**
   - No automated end-to-end test for complete flow
   - Manual testing steps not documented clearly
   - Need validation scripts to verify each component

---

## Architecture Overview

```
┌─────────────────┐
│   Frontend UI   │
│  (React/Vite)   │
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────────────────────────────┐
│         Backend API (FastAPI)            │
│  ┌──────────────────────────────────┐   │
│  │  Event Router                    │   │
│  │  POST /api/events/               │   │
│  └────────┬─────────────────────────┘   │
│           │                              │
│           ▼                              │
│  ┌──────────────────────────────────┐   │
│  │  Event Command Service (NEW)     │   │
│  │  - Monitor event status          │   │
│  │  - Dispatch MQTT commands        │   │
│  │  - Track VEN responses           │   │
│  └────────┬─────────────────────────┘   │
│           │                              │
│  ┌────────▼─────────────────────────┐   │
│  │  MQTT Publisher (boto3/AWS SDK)  │   │
│  └────────┬─────────────────────────┘   │
└───────────┼─────────────────────────────┘
            │ MQTT Publish
            ▼
┌─────────────────────────────────────────┐
│         AWS IoT Core                     │
│  Topic: ven/cmd/{venId}                 │
└────────┬──────────────┬─────────────────┘
         │              │
         │ Subscribe    │ Publish (ack, telemetry)
         ▼              ▼
┌─────────────────┐    ┌──────────────────┐
│  VEN (Enhanced) │    │  Backend MQTT    │
│                 │    │  Consumer        │
│ - Receive cmd   │    │  (gmqtt)         │
│ - Shed loads    │    └────────┬─────────┘
│ - Publish ack   │             │
│ - Send telemetry│             │ Persist
└─────────────────┘             ▼
                    ┌─────────────────────┐
                    │   PostgreSQL DB     │
                    │ - VENs              │
                    │ - Events            │
                    │ - Telemetry         │
                    │ - Load Samples      │
                    └─────────────────────┘
```

---

## Implementation Tasks

### Task 1: Backend Event Command Service
**File**: `ecs-backend/app/services/event_command_service.py`

**Functionality**:
1. Background task that monitors active events
2. When event starts (status changes to "active"):
   - Fetch all registered VENs
   - Calculate requested reduction per VEN (equal distribution or weighted)
   - Publish `shedPanel` command to each VEN via MQTT
3. When event ends:
   - Publish command to restore loads
4. Track acknowledgments and update event metrics

**Implementation Steps**:
- [ ] Create `EventCommandService` class with lifespan integration
- [ ] Add AWS IoT Data client for MQTT publishing (using boto3)
- [ ] Implement event monitoring loop (poll every 5-10 seconds)
- [ ] Add command publishing logic with proper payload structure
- [ ] Add error handling and retry logic
- [ ] Integrate with FastAPI lifespan in `main.py`

**Dependencies**:
```python
import boto3
import json
from datetime import datetime, timezone
from typing import List
```

**Key Methods**:
```python
async def start(self):
    """Start monitoring events"""

async def stop(self):
    """Stop service gracefully"""

async def _monitor_events(self):
    """Main loop to check event status"""

async def _dispatch_event_start(self, event: Event, vens: List[VEN]):
    """Send shedPanel commands when event starts"""

async def _dispatch_event_stop(self, event: Event, vens: List[VEN]):
    """Send restore commands when event ends"""

def _publish_command(self, ven_id: str, command: dict):
    """Publish MQTT command via AWS IoT Core"""
```

### Task 2: VEN Load Shedding Enhancement
**File**: `volttron-ven/ven_local_enhanced.py`

**Enhancements**:
1. **Improved `shedPanel` Handler**:
   - Calculate target power reduction
   - Apply priority-based load curtailment
   - Update shadow with event participation
   - Track event duration and auto-restore

2. **Baseline Calculation**:
   - Store recent power history (circular buffer)
   - Calculate baseline from pre-event average
   - Use for accurate `shedPowerKw` reporting

3. **Load Curtailment Strategy**:
   - Priority 1: EV charger (if not critical)
   - Priority 2: Water heater (thermal storage)
   - Priority 3: HVAC setpoint adjustment
   - Priority 4: Non-critical circuits
   - Priority 5: Battery discharge (if available)

**Implementation Steps**:
- [ ] Add `power_history` circular buffer (last 30 minutes)
- [ ] Implement `calculate_baseline()` method
- [ ] Enhance `handle_shed_panel()` with priority logic
- [ ] Add event timer for auto-restoration
- [ ] Update telemetry payload with event metrics
- [ ] Add logging for debugging

### Task 3: End-to-End Test Script
**File**: `tests/test_e2e_event_flow.py`

**Test Flow**:
1. Register test VEN in backend
2. Start test VEN locally
3. Create event via backend API
4. Monitor MQTT for command dispatch
5. Verify VEN receives command
6. Verify VEN sheds loads
7. Verify VEN sends acknowledgment
8. Verify telemetry shows reduced power
9. Wait for event end
10. Verify loads restored

**Implementation Steps**:
- [ ] Create test script with pytest
- [ ] Add fixtures for VEN registration
- [ ] Add utilities for MQTT monitoring
- [ ] Add assertions for each step
- [ ] Add cleanup to restore state

### Task 4: Helper Scripts

#### `scripts/create_test_event.py`
- Create event via backend API
- Use realistic parameters
- Print event ID for tracking

#### `scripts/test_full_flow.sh`
- Bash script to orchestrate full test
- Start VEN in background
- Create event
- Monitor logs
- Cleanup

---

## Testing Sequence

### Prerequisites
```bash
# Terminal 1: Backend running
cd ecs-backend
source venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2: VEN running
cd volttron-ven
./run_enhanced.sh

# Terminal 3: Monitoring
cd scripts
python3 ven_acks_listen.py --ven-id $THING_NAME --endpoint $IOT_ENDPOINT
```

### Manual Test Flow

#### Step 1: Register VEN
```bash
cd scripts
python3 register_ven.py \
  --backend-url http://localhost:8000 \
  --ven-id my-test-ven \
  --name "Test VEN" \
  --status online
```

**Expected**: VEN appears in backend database

#### Step 2: Start VEN
```bash
cd volttron-ven
export IOT_THING_NAME=my-test-ven
./run_enhanced.sh
```

**Expected**: 
- VEN connects to AWS IoT Core
- Telemetry publishes every 5 seconds
- Web UI accessible at http://localhost:8080

#### Step 3: Verify Telemetry
```bash
# In another terminal
cd scripts
python3 ven_telemetry_listen.py --ven-id my-test-ven
```

**Expected**: See JSON telemetry payloads every 5 seconds

#### Step 4: Create Event
```bash
curl -X POST http://localhost:8000/api/events/ \
  -H "Content-Type: application/json" \
  -d '{
    "status": "scheduled",
    "startTime": "2025-10-18T10:00:00Z",
    "endTime": "2025-10-18T11:00:00Z",
    "requestedReductionKw": 2.0
  }'
```

**Expected**: Event created with ID `evt-xxxxxxxx`

#### Step 5: Monitor Command Dispatch
```bash
# Watch backend logs
# When event becomes active, should see:
# "Publishing shedPanel command to VEN my-test-ven"
```

**Expected**: Backend publishes command when event starts

#### Step 6: Verify VEN Response
```bash
# Monitor acks
python3 ven_acks_listen.py --ven-id my-test-ven
```

**Expected**:
- Acknowledgment message received
- `ok: true`
- `data` contains `targetKw`, `acceptedReduceKw`, `until`

#### Step 7: Verify Load Shedding
- Open VEN UI: http://localhost:8080
- Check that loads are disabled/reduced
- Check event banner shows active event

**Expected**:
- EV charger disabled
- HVAC reduced
- Power usage dropped by ~2 kW

#### Step 8: Verify Telemetry During Event
```bash
# Monitor telemetry
python3 ven_telemetry_listen.py --ven-id my-test-ven
```

**Expected**:
- `eventId` field populated
- `shedPowerKw` shows reduction amount
- `usedPowerKw` lower than baseline

#### Step 9: Event Completion
- Wait for event to end OR manually stop:
```bash
curl -X POST http://localhost:8000/api/events/{event_id}/stop
```

**Expected**:
- Backend sends restore command
- VEN re-enables loads
- Telemetry shows normal power

#### Step 10: Verify Event Metrics
```bash
curl http://localhost:8000/api/events/{event_id}/metrics
```

**Expected**:
```json
{
  "currentReductionKw": 2.1,
  "vensResponding": 1,
  "avgResponseMs": 245
}
```

---

## Validation Checklist

### Backend Validation
- [ ] Event API creates events successfully
- [ ] Event command service starts with app
- [ ] Commands published to AWS IoT Core
- [ ] MQTT consumer receives telemetry
- [ ] Telemetry persisted to database
- [ ] Event metrics calculated correctly

### VEN Validation
- [ ] VEN connects to AWS IoT Core
- [ ] VEN subscribes to command topic
- [ ] VEN receives commands
- [ ] VEN sheds loads based on priority
- [ ] VEN publishes acknowledgments
- [ ] VEN publishes telemetry with event data
- [ ] VEN restores loads after event
- [ ] Web UI reflects current state

### Integration Validation
- [ ] Event creation triggers command
- [ ] Command reaches VEN within 2 seconds
- [ ] VEN responds within 5 seconds
- [ ] Load shedding achieves target reduction
- [ ] Telemetry shows accurate reduction
- [ ] Event metrics updated in real-time
- [ ] Multiple VENs can participate simultaneously

---

## Known Issues & Mitigations

### Issue 1: Network Connectivity
**Symptom**: VEN cannot connect to AWS IoT Core  
**Error**: `[Errno 101] Network is unreachable`  
**Mitigation**: 
- Check security group rules
- Verify VPC endpoints for IoT Core
- Test with `curl` to IoT endpoint

### Issue 2: Certificate Handling
**Symptom**: TLS handshake failures  
**Mitigation**:
- Verify certificates fetched from Secrets Manager
- Check file permissions (600 for private key)
- Validate certificate chain

### Issue 3: Timing Issues
**Symptom**: Event starts but command not dispatched  
**Mitigation**:
- Add event transition detection in service
- Use database triggers for event status changes
- Add monitoring logs

---

## Performance Targets

- **Command Latency**: < 2 seconds from event start to VEN command receipt
- **Response Time**: < 5 seconds from command to acknowledgment
- **Load Shed Time**: < 10 seconds from command to load reduction
- **Telemetry Frequency**: 5-10 seconds per VEN
- **Event Accuracy**: ±5% of requested reduction
- **Scalability**: Support 100+ VENs per event

---

## Next Steps

1. **Immediate** (Today):
   - Create `EventCommandService` skeleton
   - Test manual MQTT command publishing
   - Verify VEN command handling

2. **Short-term** (This Week):
   - Complete EventCommandService implementation
   - Enhance VEN load shedding
   - Create automated test script
   - Run end-to-end tests

3. **Medium-term** (Next Week):
   - Add baseline calculation
   - Improve M&V accuracy
   - Add frontend event dashboard
   - Load test with multiple VENs

4. **Documentation**:
   - Update README with new features
   - Document API changes
   - Create operator guide
   - Add troubleshooting section

---

## Success Criteria

The implementation is complete when:
1. ✅ Events created via API automatically trigger VEN commands
2. ✅ VENs receive and acknowledge commands within 5 seconds
3. ✅ VENs shed loads achieving 90%+ of requested reduction
4. ✅ Telemetry reflects actual power reduction during events
5. ✅ Event metrics show accurate aggregation across VENs
6. ✅ All integration tests pass
7. ✅ Documentation updated and validated

---

## Resources

### Documentation
- [VEN Contract](./ven-contract.md) - MQTT payload schemas
- [Testing Guide](./testing.md) - Current test procedures
- [Backend API](./backend-api.md) - API specifications

### Code References
- Backend: `ecs-backend/app/routers/event.py`
- VEN: `volttron-ven/ven_local_enhanced.py`
- MQTT Consumer: `ecs-backend/app/services/mqtt_consumer.py`
- Scripts: `scripts/ven_cmd_publish.py`, `scripts/send_event.py`

### AWS Resources
- IoT Core Endpoint: From Terraform output `iot_endpoint`
- Thing Name: From Terraform output `thing_name`
- Region: `us-west-2` (default)
