# DR Event Flow: Frontend → Backend → VEN

This document explains the complete demand response (DR) event flow with detailed circuit curtailment tracking.

> **See also**:
> - [MQTT Topics Architecture](mqtt-topics-architecture.md) - Complete MQTT topic reference and data flow
> - [Backend API](backend-api.md) - REST API endpoints for event management
> - [VEN Contract](ven-contract.md) - MQTT payload schemas

## Architecture Overview

```
┌──────────┐    REST     ┌─────────┐    MQTT      ┌──────┐
│ Frontend │────────────→│ Backend │─────────────→│ VEN  │
│ Dashboard│             │   API   │   cmd topic  │      │
└──────────┘             └─────────┘              └──────┘
                              ↑                        │
                              │      MQTT ACK topic    │
                              └────────────────────────┘
```

## Flow Breakdown

### 1. **Frontend Creates Event** (REST API)

The frontend dashboard (React app) sends a POST request to create a DR event:

```bash
curl -X POST "http://<BACKEND_ALB_URL>/api/events/" \
  -H "Content-Type: application/json" \
  -d '{
    "startTime": "2025-10-20T15:00:00Z",
    "endTime": "2025-10-20T16:00:00Z",
    "requestedReductionKw": 10.0,
    "status": "active"
  }'
```

**Response:**
```json
{
  "id": "evt-a1b2c3d4",
  "status": "active",
  "startTime": "2025-10-20T15:00:00Z",
  "endTime": "2025-10-20T16:00:00Z",
  "requestedReductionKw": 10.0,
  "actualReductionKw": 0.0
}
```

**What Happens:**
- Backend stores event in PostgreSQL database
- EventCommandService (background service) detects new active event
- Event status: `scheduled` → `active` when start time is reached

---

### 2. **Backend Publishes MQTT Command**

The `EventCommandService` runs in the background, monitoring for active events. When an event starts:

1. **Fetches all online VENs** from database
2. **Calculates reduction per VEN** (e.g., 10 kW ÷ 2 VENs = 5 kW each)
3. **Publishes MQTT command** to each VEN

**MQTT Topic:** `ven/cmd/{venId}`

**Payload:**
```json
{
  "op": "event",
  "correlationId": "evt-a1b2c3d4-abc12345",
  "venId": "volttron_thing",
  "event_id": "evt-a1b2c3d4",
  "shed_kw": 5.0,
  "duration_sec": 3600,
  "data": {
    "event_id": "evt-a1b2c3d4",
    "requestedReductionKw": 5.0,
    "duration_s": 3600
  }
}
```

**Key Field:**
- `correlationId`: Unique identifier linking this command to future ACK responses
  - Format: `evt-{eventId}-{randomHash}`
  - Enables tracking which VEN responded to which command
  - Critical for multi-VEN coordination

---

### 3. **VEN Receives Command & Applies Curtailment**

VEN subscribes to `ven/cmd/{venId}` topic and processes incoming commands:

1. **Receives MQTT message**
2. **Applies curtailment** using priority order:
   - EV Charger (100% shed)
   - Water Heater (100% shed)
   - Dryer (100% shed)
   - Electric Range (80% shed)
   - General Outlets (70% shed)
   - Lighting (50% shed)
   - **NEVER** shed critical loads (HVAC, Refrigerator)

3. **Tracks which circuits were curtailed:**
   - Circuit ID, name, breaker amps
   - Original power, curtailed amount, final power
   - Critical flag

**Example Circuit Curtailment:**
```python
circuits_curtailed = [
  {
    "id": "ev1",
    "name": "EV Charger",
    "breaker_amps": 50,
    "original_kw": 8.5,
    "curtailed_kw": 8.5,
    "final_kw": 0.0,
    "critical": false
  },
  {
    "id": "heater1",
    "name": "Water Heater",
    "breaker_amps": 30,
    "original_kw": 3.2,
    "curtailed_kw": 3.2,
    "final_kw": 0.0,
    "critical": false
  }
]
```

---

### 4. **VEN Sends ACK Response**

After applying curtailment, VEN publishes acknowledgment to backend.

**MQTT Topic:** `ven/ack/{venId}`

**Payload:**
```json
{
  "op": "event",
  "status": "accepted",
  "event_id": "evt-a1b2c3d4",
  "correlationId": "evt-a1b2c3d4-abc12345",
  "requested_shed_kw": 5.0,
  "actual_shed_kw": 5.0,
  "circuits_curtailed": [
    {
      "id": "ev1",
      "name": "EV Charger",
      "breaker_amps": 50,
      "original_kw": 8.5,
      "curtailed_kw": 8.5,
      "final_kw": 0.0,
      "critical": false
    },
    {
      "id": "heater1",
      "name": "Water Heater",
      "breaker_amps": 30,
      "original_kw": 3.2,
      "curtailed_kw": 3.2,
      "final_kw": 0.0,
      "critical": false
    }
  ],
  "ts": 1698765432
}
```

**Key Fields:**
- `correlationId`: Matches the command ID (enables request-response pairing)
- `actual_shed_kw`: What the VEN actually achieved
- `circuits_curtailed`: Detailed breakdown of which circuits were shed

---

### 5. **Backend Stores ACK & Tracks Response**

Backend's `MQTTConsumer` subscribes to `ven/ack/+` (wildcard for all VENs):

1. **Receives ACK message**
2. **Parses payload**
3. **Stores in `ven_acks` database table:**
   - `ven_id`: Which VEN responded
   - `event_id`: Which event this is for
   - `correlation_id`: Links to original command
   - `actual_shed_kw`: Performance metric
   - `circuits_curtailed`: JSON array with detailed circuit info
   - `timestamp`: When ACK was received

**Database Schema:**
```sql
CREATE TABLE ven_acks (
    id SERIAL PRIMARY KEY,
    ven_id VARCHAR(255) NOT NULL,
    event_id VARCHAR(255) NOT NULL,
    correlation_id VARCHAR(255),
    op VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    requested_shed_kw FLOAT,
    actual_shed_kw FLOAT,
    circuits_curtailed JSON,
    raw_payload TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_ven_acks_ven_id ON ven_acks(ven_id);
CREATE INDEX ix_ven_acks_event_id ON ven_acks(event_id);
CREATE INDEX ix_ven_acks_correlation_id ON ven_acks(correlation_id);
CREATE INDEX ix_ven_acks_timestamp ON ven_acks(timestamp);
```

---

## Complete Curl Example

### Prerequisites

1. **Backend deployed and running**
2. **VEN connected to MQTT** (subscribing to `ven/cmd/{venId}`)
3. **Backend environment variables set:**
   ```bash
   IOT_ENDPOINT=your-iot-endpoint.iot.us-west-2.amazonaws.com
   EVENT_COMMAND_ENABLED=true
   MQTT_ENABLED=true
   ```

### Step-by-Step Test

```bash
# 1. Get backend URL (if deployed via Terraform)
cd envs/dev
terraform output backend_alb_dns

# Example: backend-alb-1234567890.us-west-2.elb.amazonaws.com

# 2. Create DR Event (with timestamps 1 minute from now)
START_TIME=$(date -u -d '+1 minute' +%Y-%m-%dT%H:%M:%SZ)
END_TIME=$(date -u -d '+1 hour' +%Y-%m-%dT%H:%M:%SZ)

curl -X POST "http://backend-alb-1234567890.us-west-2.elb.amazonaws.com/api/events/" \
  -H "Content-Type: application/json" \
  -d "{
    \"startTime\": \"$START_TIME\",
    \"endTime\": \"$END_TIME\",
    \"requestedReductionKw\": 8.0,
    \"status\": \"scheduled\"
  }"

# Response will include event_id (e.g., evt-a1b2c3d4)

# 3. EventCommandService will automatically:
#    - Wait until START_TIME
#    - Publish command to ven/cmd/volttron_thing
#    - Include correlationId for tracking

# 4. VEN receives command and sends ACK to ven/ack/volttron_thing

# 5. Query ACKs from backend (future API endpoint)
curl "http://backend-alb-1234567890.us-west-2.elb.amazonaws.com/api/events/evt-a1b2c3d4/acks"
```

---

## What is `correlationId`?

The `correlationId` is a **request-response tracking identifier** used in asynchronous messaging:

### Purpose:
- **Links commands to responses** - Matches MQTT command with VEN ACK
- **Multi-VEN tracking** - When sending to 10 VENs, know which one responded
- **Debugging** - Trace message flow through system
- **Performance metrics** - Calculate response time per VEN

### Format:
```
evt-{eventId}-{randomHash}
```

### Example Flow:
```
Backend sends command:
  correlationId: "evt-abc123-x7y9z2"
  → ven/cmd/ven1

VEN1 responds:
  correlationId: "evt-abc123-x7y9z2"  ← Same ID!
  → ven/ack/ven1

Backend matches:
  "Ah, ven1 responded to event abc123"
```

---

## Local VEN Testing (UI-triggered events)

The VEN web UI (http://localhost:8080) has a "DER / Events" tab for **local testing only**.

**Important:** UI-triggered events do NOT go through the backend flow:
```
VEN UI → Direct Python function call → No MQTT → No backend tracking
```

**Event ID format:**
- Backend events: `evt-{uuid}` (e.g., `evt-a1b2c3d4`)
- Local UI events: `ui-evt-{timestamp}` (e.g., `ui-evt-1760916447`)

**For production testing, always use the backend API!**

---

## Post-Event Analysis

With circuit-level tracking, you can now answer:

1. **Which circuits were actually shed?**
   ```sql
   SELECT circuits_curtailed 
   FROM ven_acks 
   WHERE event_id = 'evt-abc123';
   ```

2. **How much did each VEN contribute?**
   ```sql
   SELECT ven_id, actual_shed_kw 
   FROM ven_acks 
   WHERE event_id = 'evt-abc123';
   ```

3. **Were critical loads protected?**
   ```sql
   SELECT ven_id, 
          jsonb_array_elements(circuits_curtailed::jsonb) AS circuit
   FROM ven_acks 
   WHERE event_id = 'evt-abc123' 
     AND circuits_curtailed::jsonb @> '[{"critical": true}]';
   ```

4. **Response time per VEN:**
   ```sql
   SELECT ven_id, 
          timestamp - (SELECT start_time FROM events WHERE event_id = 'evt-abc123') AS response_time
   FROM ven_acks 
   WHERE event_id = 'evt-abc123';
   ```

---

## Next Steps

1. **Run database migration:**
   ```bash
   cd ecs-backend
   alembic upgrade head
   ```

2. **Deploy updated backend:**
   ```bash
   cd ecs-backend
   ./build_and_push.sh
   cd ../envs/dev
   terraform apply
   ```

3. **Test the flow:**
   ```bash
   # Use curl command above to create event
   # Watch VEN logs: tail -f /tmp/ven_enhanced.log
   # Check backend logs: docker logs <container>
   ```

4. **Add API endpoints** (future work):
   - `GET /api/events/{eventId}/acks` - List all ACKs for an event
   - `GET /api/vens/{venId}/acks` - List all ACKs from a VEN
   - `GET /api/events/{eventId}/circuits` - Circuit breakdown for event

---

## Troubleshooting

**Event not triggering?**
- Check `EVENT_COMMAND_ENABLED=true` in backend env
- Verify `IOT_ENDPOINT` is set correctly
- Check EventCommandService logs: "Event {id} is starting"

**VEN not receiving commands?**
- Verify VEN subscribes to `ven/cmd/{venId}`
- Check AWS IoT Core policy allows publish to this topic
- VEN logs should show: "📨 Command received: event"

**ACKs not stored in database?**
- Check backend subscribes to `ven/ack/+`
- Verify `MQTT_ENABLED=true` in backend
- Look for "Persisted VEN ACK" in backend logs

**correlationId not matching?**
- VEN must include exact `correlationId` from command in ACK
- Check VEN code: `ack["correlationId"] = payload.get("correlationId")`
