# VEN Stability Improvement Plan - Progress Report

## Date: October 15, 2025

## Executive Summary

Following a systematic 3-step plan to achieve VEN MQTT stability by mirroring the backend's proven thread-safe architecture.

---

## ✅ STEP 1: Backend MQTT Stability Baseline

**Status: COMPLETE**

### Results:
```
MQTT errors in last 12 hours: 0
Library: gmqtt (async, thread-safe)
Connection: Stable, zero disconnects
```

### Key Findings:
1. **Backend uses gmqtt** (`ecs-backend/app/services/mqtt_consumer.py`)
   - Async/await pattern
   - No manual thread management (`loop_start()`)
   - Built-in thread safety

2. **Architecture Pattern:**
   ```python
   # Backend's approach:
   client = gmqtt.Client(client_id)
   await client.connect(host, port, ssl=ssl_context)
   # Callbacks handled in event loop automatically
   ```

3. **Certificate Handling:**
   - Uses AWS Secrets Manager for TLS certs
   - Creates temporary files from PEM content
   - Secrets ARN: `dev-backend-tls-3TLn49`

### Conclusion:
**Backend's gmqtt-based approach is 100% stable** - this is our target architecture.

---

## 🔄 STEP 2: Simplify VEN with Thread-Safe MQTT

**Status: IN PROGRESS**

### Completed:
1. ✅ Created `ven_simple.py` - mirrors backend pattern
2. ✅ Added `gmqtt==0.6.12` to requirements
3. ✅ Created `Dockerfile.simple` for isolated testing
4. ✅ Built and pushed to ECR: `volttron-ven:simple-latest`
5. ✅ Removed complex components:
   - No HTML UI
   - No device_simulator initially
   - No Flask server (will add back later)
   - Focus: MQTT connection stability only

### Architecture Comparison:

| Aspect | Current VEN (ven_agent.py) | Simplified VEN (ven_simple.py) |
|--------|---------------------------|--------------------------------|
| **Library** | paho-mqtt | gmqtt (like backend) |
| **Threading** | Manual (`loop_start()`) | Async/await (automatic) |
| **Callbacks** | Synchronous | Async-safe |
| **Complexity** | 2186 lines | ~210 lines |
| **UI** | Flask + HTML | None (testing only) |
| **Device Sim** | Complex 8-load simulator | Simple single value |

### Next Actions for Step 2:
1. ⏳ Configure AWS Secrets for simplified VEN
2. ⏳ Deploy to ECS and monitor for 1 hour
3. ⏳ Verify zero disconnects (target: same as backend)
4. ⏳ Test backend command reception

---

## 📋 STEP 3: Expand Gradually (NOT STARTED)

**Status: PENDING** (waiting for Step 2 stability)

### Planned Additions (in order):
1. **Phase 3.1:** Add Flask health endpoints (`/health`, `/live`)
   - Keep it minimal
   - No HTML UI yet

2. **Phase 3.2:** Add device simulator back
   - Start with 1-2 loads only
   - Monitor stability

3. **Phase 3.3:** Add all loads (HVAC, EV, battery, etc.)
   - Gradual expansion
   - Monitor after each addition

4. **Phase 3.4:** Add backend command handling
   - `ping`, `shedLoad`, `event`
   - Test DR event flow

5. **Phase 3.5:** Consider adding HTML UI
   - **Decision Point:** Do we need `sim.gridcircuit.link`?
   - Alternative: Use frontend for visualization

---

## Technical Debt & Decisions

### Issues with Current VEN (ven_agent.py):
1. **Multiple MQTT threading issues** (6 root causes fixed in previous session)
2. **paho-mqtt** requires manual thread management
3. **Complex initialization order** dependencies
4. **2186 lines** - hard to debug

### Decision: Fresh Start vs. Fix
**Chosen approach:** Fresh start with proven pattern
- **Rationale:** Backend has 0 errors in 12 hours with gmqtt
- **Risk:** Lower - we're copying a working implementation
- **Timeline:** Faster than debugging 2186 lines

### Open Questions:
1. **Do we need the HTML UI (`sim.gridcircuit.link`)?**
   - Current UI is at `http://volttron-alb-*.elb.amazonaws.com`
   - Frontend exists: `http://frontend-alb-*.elb.amazonaws.com`
   - **Recommendation:** Use frontend for visualization, remove VEN UI

2. **Device simulator complexity?**
   - Current: 8 loads with complex state management
   - **Proposal:** Start with simple telemetry, add loads incrementally

---

## Success Criteria

### Step 2 Success Metrics:
- [ ] Simplified VEN connects to AWS IoT Core
- [ ] Zero unexpected disconnects for 1 hour
- [ ] Publishes telemetry every 30 seconds
- [ ] Backend receives and stores telemetry
- [ ] Receives backend commands (ping test)

### Step 3 Success Metrics:
- [ ] All components (UI, simulator, commands) working
- [ ] Still zero unexpected disconnects
- [ ] DR event end-to-end flow validated
- [ ] Load shedding reflected in telemetry
- [ ] Backend logs load reductions

---

## Next Immediate Steps

1. **Configure simplified VEN secrets:**
   ```bash
   # Update ECS task definition with:
   # - secrets: dev-backend-tls-3TLn49 (CA_CERT_PEM, CLIENT_CERT_PEM, PRIVATE_KEY_PEM)
   # - environment: MQTT_HOST, MQTT_PORT=8883, MQTT_USE_TLS=true
   ```

2. **Deploy to ECS:**
   ```bash
   aws ecs update-service --cluster hems-ecs-cluster \
     --service volttron-ven --desired-count 1 \
     --task-definition <new-task-def-with-simple-image>
   ```

3. **Monitor for 1 hour:**
   ```bash
   aws logs tail /ecs/volttron-ven --follow | \
     grep -E "connected|disconnect|ERROR"
   ```

4. **Send test command:**
   ```bash
   python scripts/ven_cmd_publish.py \
     --ven-id volttron_thing \
     --endpoint a1mgxpe8mg484j-ats.iot.us-west-2.amazonaws.com \
     --op ping
   ```

---

## Files Created/Modified

### New Files:
- `volttron-ven/ven_simple.py` - Simplified VEN (210 lines)
- `volttron-ven/Dockerfile.simple` - Build container
- `volttron-ven/deploy_simple.sh` - Deployment script
- `volttron-ven/VEN_STABILITY_PLAN.md` - This document

### Modified Files:
- `volttron-ven/requirements.txt` - Added gmqtt
- `volttron-ven/ven_agent.py` - Added debug logging (committed separately)

### Git Commits:
1. `37e7373` - Add debug logging to backend command handler
2. `e0aff67` - WIP: Create simplified VEN with thread-safe MQTT

---

## References

### Backend MQTT Implementation:
- File: `ecs-backend/app/services/mqtt_consumer.py`
- Pattern: Async/await with gmqtt
- Stability: 0 errors in 12+ hours

### AWS Resources:
- IoT Endpoint: `a1mgxpe8mg484j-ats.iot.us-west-2.amazonaws.com:8883`
- Secret: `arn:aws:secretsmanager:us-west-2:923675928909:secret:dev-backend-tls-3TLn49`
- ECS Cluster: `hems-ecs-cluster`
- ECS Service: `volttron-ven`

### Topics:
- Telemetry: `ven/telemetry/volttron_thing`
- Commands: `ven/cmd/volttron_thing`
- Load Samples: `ven/loads/volttron_thing`

---

**Last Updated:** 2025-10-15 18:00 UTC
**Status:** Step 2 in progress - ready for secrets configuration and deployment
