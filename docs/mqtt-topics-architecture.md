# MQTT Topics Architecture

## Overview

This document describes the MQTT topic architecture used for VEN (Virtual End Node) communication with the backend system through AWS IoT Core.

## Topic Summary

| Topic Pattern | Publisher | Subscriber | Frequency | Purpose | Backend Storage |
|--------------|-----------|------------|-----------|---------|-----------------|
| `volttron/metering` | VEN | Backend (via IoT Rule) | Every 5 sec | Primary telemetry with circuit details | `VenTelemetry` + `VenLoadSample` |
| `ven/telemetry/{venId}` | VEN | External monitoring | Every 5 sec | Per-VEN monitoring/debugging | Not stored |
| `ven/ack/{venId}` | VEN | Backend | On event | Event acknowledgment with curtailment details | `VenAck` |
| `$aws/things/{venId}/shadow/update` | VEN | AWS IoT Shadow | Every 30 sec | Real-time state for UI | AWS IoT Shadow |
| `ven/loads/{venId}` | VEN | Not subscribed | Every 30 sec | Load snapshots (currently unused) | Not stored |
| `ven/cmd/{venId}` | Backend | VEN | On demand | Command/control (DR events, restore, etc.) | N/A |

## Detailed Topic Descriptions

### 1. `volttron/metering` - Primary Telemetry

**Purpose**: Main telemetry stream for backend storage and historical analysis.

**Publisher**: VEN  
**Subscriber**: Backend MQTT consumer (via AWS IoT Rule)  
**Frequency**: Every 5 seconds (continuous)  
**When**: Always running, includes event context when active  

**Payload Structure**:
```json
{
  "venId": "ven-001",
  "timestamp": 1729700000,
  "usedPowerKw": 8.2,
  "shedPowerKw": 4.8,
  "requestedReductionKw": 5.0,
  "eventId": "evt-123",
  "baselinePowerKw": 13.0,
  "batterySOC": 85.5,
  "panelAmperageRating": 200,
  "panelVoltage": 240,
  "panelMaxKw": 48.0,
  "currentAmps": 34.2,
  "panelUtilizationPercent": 17.1,
  "circuits": [
    {
      "id": "circuit_1",
      "name": "Main HVAC",
      "breakerAmps": 30,
      "currentKw": 2.1,
      "currentAmps": 8.75,
      "enabled": true,
      "critical": false
    },
    {
      "id": "circuit_3",
      "name": "Pool Pump",
      "breakerAmps": 20,
      "currentKw": 0.0,
      "currentAmps": 0.0,
      "enabled": false,
      "critical": false
    }
  ],
  "loads": [
    {
      "loadId": "circuit_1",
      "name": "Main HVAC",
      "type": "hvac",
      "capacityKw": 5.0,
      "currentPowerKw": 2.1,
      "shedCapabilityKw": 5.0,
      "enabled": true,
      "priority": 2
    }
  ]
}
```

**Backend Processing**:
- Stored in `VenTelemetry` table (aggregate telemetry per VEN per timestamp)
- Circuit-level data extracted and stored in `VenLoadSample` table (linked to `VenTelemetry`)
- Auto-registers VEN if not already in database
- Updates VEN heartbeat and online status

**Use Cases**:
- Historical power usage analysis
- Circuit-level load tracking over time
- Event performance monitoring (shed effectiveness)
- Baseline calculation for DR events
- Time-series queries via `/api/vens/{ven_id}/telemetry` endpoint
- Circuit history via `/api/vens/{ven_id}/circuits/history` endpoint

---

### 2. `ven/telemetry/{venId}` - Per-VEN Monitoring

**Purpose**: Per-VEN telemetry stream for external monitoring and debugging.

**Publisher**: VEN  
**Subscriber**: External monitoring tools, debug scripts  
**Frequency**: Every 5 seconds (continuous)  
**When**: Always running  

**Payload Structure**: Identical to `volttron/metering`

**Backend Processing**: Not subscribed, not stored

**Use Cases**:
- Monitoring specific VEN without filtering `volttron/metering` stream
- Debug scripts (e.g., `scripts/ven_telemetry_listen.py`)
- External monitoring dashboards
- Development/testing isolation

**Note**: This topic contains duplicate data from `volttron/metering`. It exists for convenience and does not add storage overhead since the backend does not subscribe to it.

---

### 3. `ven/ack/{venId}` - Event Acknowledgment

**Purpose**: VEN acknowledgment of received commands, especially DR events.

**Publisher**: VEN  
**Subscriber**: Backend MQTT consumer  
**Frequency**: On-demand (when command received)  
**When**: In response to commands on `ven/cmd/{venId}`  

**Payload Structure** (Event ACK):
```json
{
  "op": "event",
  "status": "accepted",
  "event_id": "evt-123",
  "requested_shed_kw": 5.0,
  "actual_shed_kw": 4.8,
  "circuits_curtailed": [
    {
      "loadId": "circuit_3",
      "name": "HVAC",
      "shedKw": 3.5
    },
    {
      "loadId": "circuit_5",
      "name": "Pool Pump",
      "shedKw": 1.3
    }
  ],
  "ts": 1729700000,
  "correlationId": "xyz-123"
}
```

**Payload Structure** (Restore ACK):
```json
{
  "op": "restore",
  "status": "success",
  "ts": 1729700000,
  "correlationId": "xyz-456"
}
```

**Backend Processing**:
- Stored in `VenAck` table
- Includes which circuits were curtailed and by how much
- Links event_id to actual curtailment actions
- Used for event history and compliance reporting

**Backend Subscription**: `ven/ack/+` (wildcard subscribes to all VENs)

**Use Cases**:
- Event history display in UI (`/api/vens/{ven_id}/events` endpoint)
- Compliance reporting (did VEN accept/reject event?)
- Curtailment verification (actual vs requested shed)
- Audit trail for DR events

---

### 4. `$aws/things/{venId}/shadow/update` - Device Shadow

**Purpose**: AWS IoT Device Shadow for real-time state synchronization.

**Publisher**: VEN  
**Subscriber**: AWS IoT Core Shadow service  
**Frequency**: Every 30 seconds (every 6th telemetry cycle)  
**When**: Always running  

**Payload Structure**:
```json
{
  "state": {
    "reported": {
      "power_kw": 8.2,
      "shed_kw": 4.8,
      "panel_amperage": 200,
      "panel_voltage": 240,
      "panel_max_kw": 48.0,
      "circuits": [
        {
          "id": "circuit_1",
          "name": "Main HVAC",
          "enabled": true,
          "available": true,
          "current_kw": 2.1,
          "breaker_amps": 30,
          "current_amps": 8.75,
          "critical": false
        }
      ],
      "active_event": {
        "event_id": "evt-123",
        "shed_kw": 5.0,
        "end_ts": 1729703600
      },
      "timestamp": 1729700000
    }
  }
}
```

**Backend Processing**: 
- Managed by AWS IoT Core
- Shadow state retrieved via `/api/vens/{ven_id}/shadow` endpoint
- Frontend polls shadow for real-time UI updates

**Use Cases**:
- Real-time VEN status display in UI
- Current circuit states
- Active event visualization
- Latest snapshot without database query

---

### 5. `ven/loads/{venId}` - Load Snapshots (Unused)

**Purpose**: Circuit-level load snapshots (currently not subscribed by backend).

**Publisher**: VEN  
**Subscriber**: None (backend not configured to subscribe)  
**Frequency**: Every 30 seconds (every 6th telemetry cycle)  
**When**: Always running  

**Payload Structure**:
```json
{
  "schemaVersion": "1.0",
  "venId": "ven-001",
  "timestamp": 1729700000,
  "loads": [
    {
      "loadId": "circuit_1",
      "name": "Main HVAC",
      "type": "hvac",
      "capacityKw": 5.0,
      "currentPowerKw": 2.1,
      "shedCapabilityKw": 5.0,
      "enabled": true,
      "priority": 2
    }
  ]
}
```

**Backend Processing**: 
- Handler exists (`_persist_load_snapshot()` in `mqtt_consumer.py`)
- Would store in `LoadSnapshot` table if subscribed
- Currently **NOT** subscribed (backend_loads_topic=None)

**Status**: **REDUNDANT** - Circuit data already captured in `volttron/metering` every 5 seconds and stored in `VenLoadSample` table.

**Note**: This topic was added for circuit history but is unnecessary since `volttron/metering` already provides more frequent circuit-level data.

---

### 6. `ven/cmd/{venId}` - Command/Control

**Purpose**: Backend sends commands to VEN (DR events, restore, etc.).

**Publisher**: Backend  
**Subscriber**: VEN  
**Frequency**: On-demand  
**When**: User-initiated or automated DR events  

**Payload Structure** (DR Event):
```json
{
  "op": "event",
  "event_id": "evt-123",
  "shed_kw": 5.0,
  "duration_sec": 3600,
  "correlationId": "xyz-123",
  "data": {
    "requestedReductionKw": 5.0,
    "duration_s": 3600
  }
}
```

**Payload Structure** (Restore):
```json
{
  "op": "restore",
  "correlationId": "xyz-456"
}
```

**Payload Structure** (Ping):
```json
{
  "op": "ping",
  "correlationId": "xyz-789"
}
```

**VEN Processing**:
- Receives command via MQTT subscription
- Processes in `handle_command()` function
- Applies curtailment or restoration
- Publishes ACK to `ven/ack/{venId}`

**Backend API**: `/api/vens/{ven_id}/send-event` endpoint publishes to this topic

**Use Cases**:
- Sending DR events to VEN
- Manual restoration of circuits
- Health check (ping/pong)

---

## Data Flow During DR Event

### Phase 1: Event Initiation
1. Backend publishes event command to `ven/cmd/{venId}`
2. VEN receives command, applies curtailment
3. VEN publishes acknowledgment to `ven/ack/{venId}` with circuit details
4. Backend stores ACK in `VenAck` table

### Phase 2: During Event (Continuous)
1. VEN publishes telemetry every 5 seconds to `volttron/metering` with `eventId`
2. Backend stores in `VenTelemetry` + `VenLoadSample` tables
3. VEN updates shadow every 30 seconds with active event info
4. Frontend polls shadow for real-time updates

### Phase 3: Event End
1. Event duration expires OR backend sends restore command
2. VEN restores circuits to normal operation
3. VEN publishes restore ACK to `ven/ack/{venId}`
4. VEN continues normal telemetry without `eventId`

---

## Backend Subscription Configuration

**File**: `ecs-backend/app/core/config.py`

```python
# MQTT Topics the backend subscribes to
mqtt_topic_metering: str = Field("volttron/metering")
mqtt_topic_status: str | None = Field(None)
mqtt_topic_events: str | None = Field(None)
mqtt_topic_responses: str | None = Field(None)
backend_loads_topic: str | None = Field(None)  # Currently None, not used
mqtt_additional_topics: list[str] = Field(default_factory=list)

# Built dynamically, filters out None values
@property
def mqtt_topics(self) -> list[str]:
    topics = [
        self.mqtt_topic_metering,
        self.mqtt_topic_status,
        self.mqtt_topic_events,
        self.mqtt_topic_responses,
        self.backend_loads_topic,
        *self.mqtt_additional_topics,
    ]
    return [t for t in topics if t]
```

**Active Subscriptions**:
- `volttron/metering` (metering)
- `ven/ack/+` (wildcard for all VEN acknowledgments)

---

## Environment Variables

### VEN Configuration

```bash
# IoT Core endpoint
IOT_ENDPOINT=xxxxx.iot.us-east-1.amazonaws.com

# VEN identifier
CLIENT_ID=ven-001

# Topic overrides (optional, defaults shown)
TELEMETRY_TOPIC=ven/telemetry/ven-001
METERING_TOPIC=volttron/metering
LOADS_TOPIC=ven/loads/ven-001
CMD_TOPIC=ven/cmd/ven-001
ACK_TOPIC=ven/ack/ven-001

# Web UI port
WEB_PORT=8080
```

### Backend Configuration

```bash
# MQTT broker (AWS IoT Core endpoint)
MQTT_BROKER=xxxxx.iot.us-east-1.amazonaws.com
MQTT_PORT=8883

# Primary telemetry topic
MQTT_TOPIC_METERING=volttron/metering

# Optional topics (currently not used)
MQTT_TOPIC_STATUS=
MQTT_TOPIC_EVENTS=
MQTT_TOPIC_RESPONSES=
BACKEND_LOADS_TOPIC=

# Additional topics (comma-separated)
MQTT_TOPICS=
```

---

## Database Schema

### VenTelemetry Table
Stores aggregate telemetry per VEN per timestamp.

```sql
CREATE TABLE ven_telemetry (
    id SERIAL PRIMARY KEY,
    ven_id VARCHAR NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    used_power_kw FLOAT,
    shed_power_kw FLOAT,
    requested_reduction_kw FLOAT,
    event_id VARCHAR,
    battery_soc FLOAT,
    raw_payload JSON
);
```

### VenLoadSample Table
Stores per-circuit telemetry linked to VenTelemetry.

```sql
CREATE TABLE ven_load_samples (
    id SERIAL PRIMARY KEY,
    telemetry_id INTEGER REFERENCES ven_telemetry(id) ON DELETE CASCADE,
    load_id VARCHAR NOT NULL,
    name VARCHAR,
    type VARCHAR,
    capacity_kw FLOAT,
    current_power_kw FLOAT,
    shed_capability_kw FLOAT,
    enabled BOOLEAN,
    priority INTEGER,
    raw_payload JSON
);
```

### VenAck Table
Stores event acknowledgments with curtailment details.

```sql
CREATE TABLE ven_acks (
    id SERIAL PRIMARY KEY,
    ven_id VARCHAR NOT NULL,
    event_id VARCHAR,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    op VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    requested_shed_kw FLOAT,
    actual_shed_kw FLOAT,
    circuits_curtailed JSON,
    raw_payload JSON,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### LoadSnapshot Table (Unused)
Standalone circuit snapshots (handler exists but not subscribed).

```sql
CREATE TABLE load_snapshots (
    id SERIAL PRIMARY KEY,
    ven_id VARCHAR NOT NULL,
    load_id VARCHAR NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    current_power_kw FLOAT,
    shed_capability_kw FLOAT,
    enabled BOOLEAN,
    raw_payload JSON
);
```

---

## API Endpoints

### GET `/api/vens/{ven_id}/telemetry`
Returns time-series telemetry from `VenTelemetry` table.

**Query Params**: `start`, `end`, `limit`

### GET `/api/vens/{ven_id}/circuits/history`
Returns circuit-level history from `VenLoadSample` table.

**Query Params**: `load_id`, `start`, `end`, `limit`

### GET `/api/vens/{ven_id}/events`
Returns event history from `VenAck` table with circuit curtailment details.

**Query Params**: `start`, `end`, `limit`

### GET `/api/vens/{ven_id}/shadow`
Returns current Device Shadow state from AWS IoT Core.

### POST `/api/vens/{ven_id}/send-event`
Publishes DR event command to `ven/cmd/{venId}`.

---

## Monitoring Scripts

### `scripts/ven_telemetry_listen.py`
Subscribes to `ven/telemetry/{venId}` for per-VEN monitoring.

### `scripts/test_mqtt_telemetry.py`
Tests MQTT connectivity and telemetry publishing.

### `scripts/monitor_ven.py`
Monitors VEN status and telemetry.

---

## AWS IoT Rules

### Metering Rule
Forwards `volttron/metering` messages to backend MQTT consumer.

```sql
SELECT * FROM 'volttron/metering'
```

**Action**: Republish to internal MQTT broker consumed by backend.

---

## Best Practices

### Topic Naming
- Use hierarchical structure: `category/subcategory/identifier`
- Keep VEN-specific topics namespaced: `ven/{operation}/{venId}`
- Use wildcards for subscriptions: `ven/ack/+` subscribes to all VENs

### Frequency Guidelines
- **High frequency (5 sec)**: Critical telemetry, stored in database
- **Medium frequency (30 sec)**: State snapshots, UI updates
- **On-demand**: Commands, acknowledgments

### QoS Levels
- **QoS 1**: Event commands, acknowledgments (at-least-once delivery)
- **QoS 0**: Telemetry (best-effort, high frequency acceptable loss)

### Payload Size
- Keep payloads under 128KB (AWS IoT Core limit)
- Use camelCase for JSON fields
- Include `timestamp` in all messages
- Include `venId` for correlation

---

## Troubleshooting

### VEN Not Sending Telemetry
1. Check MQTT connection: Look for "🔌 Connected to AWS IoT Core" in VEN logs
2. Verify certificates: CA cert, client cert, private key
3. Check IoT endpoint: `IOT_ENDPOINT` environment variable
4. Monitor topics: Use `scripts/ven_telemetry_listen.py`

### Backend Not Receiving Telemetry
1. Check AWS IoT Rule: Is `volttron/metering` forwarded?
2. Verify subscription: Backend logs should show "Subscribed to: volttron/metering"
3. Check MQTT consumer: Is `mqtt_consumer.py` running?
4. Database connection: Check `VenTelemetry` table for recent entries

### Shadow Not Updating
1. Check shadow permissions: IoT policy must allow shadow updates
2. Verify topic: `$aws/things/{venId}/shadow/update`
3. Use AWS IoT console to view shadow document
4. Check VEN logs for shadow publish errors

---

## Future Considerations

### Potential Optimizations
1. **Remove `ven/loads/{venId}`**: Redundant with `volttron/metering`
2. **Remove `ven/telemetry/{venId}`**: Only if external monitoring not needed
3. **Reduce shadow frequency**: Consider 60 sec instead of 30 sec
4. **Batching**: Send multiple telemetry samples in single message for efficiency

### Additional Topics (Future)
- `ven/alerts/{venId}`: Critical alerts (overcurrent, offline circuits)
- `ven/diagnostics/{venId}`: Detailed diagnostic info (on-demand)
- `ven/config/{venId}`: Configuration updates from backend

---

## References

- **VEN Implementation**: `volttron-ven/ven_local_enhanced.py`
- **Backend MQTT Consumer**: `ecs-backend/app/services/mqtt_consumer.py`
- **Backend Configuration**: `ecs-backend/app/core/config.py`
- **Database Models**: `ecs-backend/app/models/telemetry.py`
- **API Endpoints**: `ecs-backend/app/routers/ven.py`

---

**Last Updated**: October 23, 2025  
**Version**: 1.0
