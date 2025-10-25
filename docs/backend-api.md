# Backend API Design

This document summarizes backend API endpoints required to support the Smart Grid Control Center dashboard and future load insights.

> **See also**:
> - [MQTT Topics Architecture](mqtt-topics-architecture.md) - MQTT topics and data flow
> - [DR Event Flow](dr-event-flow.md) - Complete DR event flow documentation
> - OpenAPI spec: `docs/backend-api.yaml`

## Data Model

- **NetworkStats** – summary metrics such as `venCount`, `controllablePowerKw`, `potentialLoadReductionKw`, and `householdUsageKw`. This shall give overall status of the VEN network. These data are expected to be aggregated in the backend returned here for overview data.
- **VEN** – a Virtual End Node with `id`, `name`, `status`, `location {lat, lon}`, `loads[]`, and `metrics` describing current power, shed availability, and Shed status (ADR event id, shed load's ids)
- **Load** – device/circuit attached to a VEN with `id`, `type`, `capacityKw`, `shedCapabilityKw`, and `currentPowerKw`.
- **Event** – ADR event with `id`, `status`, `startTime`, `endTime`, `requestedReductionKw`, and `actualReductionKw`
- **TimeseriesPoint** – VEN level and system level `{timestamp, usedPowerKw, shedPowerKw, eventId}` used in historical responses.
- **CircuitSnapshot** – Circuit-level power snapshot with `{timestamp, loadId, currentPowerKw, shedCapabilityKw, enabled}`
- **VenAck** – Event acknowledgment with circuit curtailment details

## Network Statistics

- `GET /stats/network` – current network metrics aligned to `NetworkStats` (VEN count, controllable power, potential load reduction, household usage).
- `GET /stats/loads` – aggregated capability and usage by load type (EV, solar generation, HVAC, etc.).
- `GET /stats/network/history` – historical network metrics with `start`, `end`, and optional `granularity` query parameters.

### Example

```http
GET /stats/network
```

```json
{
  "venCount": 42,
  "controllablePowerKw": 1200,
  "potentialLoadReductionKw": 300,
  "householdUsageKw": 890
}
```

## VEN Management

- `GET /api/vens` – list registered Virtual End Nodes including `id`, `name`, `status`, `location` (lat, lon), `loads[]`, and `metrics` (see below) for mapping and quick stats.
- `POST /api/vens` – register a new VEN.
- `GET /api/vens/{venId}` – fetch detailed VEN information.
- `PATCH /api/vens/{venId}` – update VEN configuration.
- `DELETE /api/vens/{venId}` – remove a VEN.
- `GET /api/vens/{venId}/shadow` – **[NEW]** get current AWS IoT Device Shadow state (real-time)
- `GET /api/vens/{venId}/telemetry` – **[NEW]** historical telemetry time-series (query params: `start`, `end`, `limit`)
- `GET /api/vens/{venId}/events` – **[NEW]** event acknowledgment history with circuit curtailment details
- `GET /api/vens/{venId}/circuits/history` – **[NEW]** circuit-level power history (query params: `load_id`, `start`, `end`, `limit`)
- `POST /api/vens/{venId}/send-event` – send DR event command via MQTT
- `GET /api/vens/{venId}/loads` – list controllable loads attached to a VEN.
- `GET /api/vens/{venId}/loads/{loadId}` – detailed load data with fields `capacityKw`, `shedCapabilityKw`, and `currentPowerKw`.
- `PATCH /api/vens/{venId}/loads/{loadId}` – update load metadata or configuration.
- `POST /api/vens/{venId}/loads/{loadId}/commands/shed` – issue a shed command for a specific load.

### Example

**Create VEN**

```http
POST /vens
```

```json
{
  "name": "Main Street Facility",
  "location": { "lat": 37.42, "lon": -122.08 }
}
```

**Response**

```json
{
  "id": "ven-123",
  "name": "Main Street Facility",
  "status": "active",
  "location": { "lat": 37.42, "lon": -122.08 },
  "loads": [],
  "metrics": {
    "currentPowerKw": 12.4,
    "shedAvailabilityKw": 5.0,
    "activeEventId": "evt-1",
    "shedLoadIds": []
  }
}
```

## ADR Event Control

- `POST /events` – start a new automated demand response event.
- `GET /events` – list events.
- `GET /events/{eventId}` – event details and progress.
- `POST /events/{eventId}/stop` – stop an active event.
- `DELETE /events/{eventId}` – cancel a pending event.
- `GET /events/current` – currently active ADR event.
- `GET /events/history` – events occurring within a time interval.

### Example

**Create Event**

```http
POST /events
```

```json
{
  "startTime": "2024-07-10T15:00:00Z",
  "endTime": "2024-07-10T17:00:00Z",
  "requestedReductionKw": 500
}
```

**Response**

```json
{
  "id": "evt-1",
  "status": "scheduled",
  "startTime": "2024-07-10T15:00:00Z",
  "endTime": "2024-07-10T17:00:00Z",
  "requestedReductionKw": 500,
  "actualReductionKw": 0
}
```

## Historical Queries

- `GET /stats/network/history` – network level history. Returns an array of `TimeseriesPoint` aligned to the data model.
- `GET /vens/{venId}/history` – VEN level history. Returns an array of `TimeseriesPoint` aligned to the data model.
- `GET /vens/{venId}/loads/{loadId}/history` – load level history. Returns an array of `TimeseriesPoint` aligned to the data model.

### Example

```http
GET /vens/ven-123/history?start=2024-07-10T15:00:00Z&end=2024-07-10T17:00:00Z&granularity=5m
```

```json
{
  "points": [
    {
      "timestamp": "2024-07-10T15:00:00Z",
      "usedPowerKw": 5.2,
      "shedPowerKw": 0.0
    },
    {
      "timestamp": "2024-07-10T15:05:00Z",
      "usedPowerKw": 5.0,
      "shedPowerKw": 0.0
    }
  ]
}
```

Note: Where a point falls within an ADR event window, implementations may also include the associated `eventId` and/or `requestedReductionKw` to annotate shed context per point.

## New Endpoints (October 2025)

### Get VEN Event History

Returns event acknowledgments with detailed circuit curtailment information.

```http
GET /api/vens/volttron_thing/events?start=2025-10-20T00:00:00Z&limit=10
```

**Response:**
```json
{
  "totalCount": 5,
  "events": [
    {
      "eventId": "evt-abc123",
      "timestamp": "2025-10-20T15:30:00Z",
      "op": "event",
      "status": "accepted",
      "requestedShedKw": 5.0,
      "actualShedKw": 4.8,
      "circuitsCurtailed": [
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
      ]
    }
  ]
}
```

### Get Circuit History

Returns time-series power data for specific circuits or all circuits.

**Query Parameters:**
- `load_id` (optional): Filter by specific circuit/load ID. Omit to get all circuits.
- `start` (optional): ISO 8601 timestamp for range start
- `end` (optional): ISO 8601 timestamp for range end
- `limit` (optional): Maximum number of snapshots to return (default: 100)

**Examples:**

Get all circuits for a VEN:
```http
GET /api/vens/volttron_thing/circuits/history?start=2025-10-20T15:00:00Z&limit=50
```

Get specific circuit history:
```http
GET /api/vens/volttron_thing/circuits/history?load_id=circuit_3&start=2025-10-20T15:00:00Z&limit=20
```

**Response:**
```json
{
  "totalCount": 20,
  "snapshots": [
    {
      "timestamp": "2025-10-20T15:30:05Z",
      "loadId": "circuit_3",
      "name": "Pool Pump",
      "currentPowerKw": 0.0,
      "shedCapabilityKw": 3.5,
      "enabled": false
    },
    {
      "timestamp": "2025-10-20T15:30:10Z",
      "loadId": "circuit_3",
      "name": "Pool Pump",
      "currentPowerKw": 0.0,
      "shedCapabilityKw": 3.5,
      "enabled": false
    }
  ]
}
```

**Note:** Snapshots are returned in descending timestamp order (newest first). The response includes circuit metadata (`name`) along with power measurements.

### Get VEN Telemetry

Returns aggregate telemetry time-series for a VEN.

**Query Parameters:**
- `start` (optional): ISO 8601 timestamp for range start
- `end` (optional): ISO 8601 timestamp for range end
- `limit` (optional): Maximum number of records to return (default: 100)

```http
GET /api/vens/volttron_thing/telemetry?start=2025-10-20T15:00:00Z&limit=10
```

**Response:**
```json
{
  "totalCount": 10,
  "telemetry": [
    {
      "timestamp": "2025-10-20T15:30:05Z",
      "usedPowerKw": 8.2,
      "shedPowerKw": 4.8,
      "requestedReductionKw": 5.0,
      "eventId": "evt-abc123",
      "batterySoc": 85.5,
      "panelAmperageRating": 200,
      "panelVoltage": 240,
      "panelMaxKw": 48.0,
      "currentAmps": 34.2,
      "panelUtilizationPercent": 17.1
    }
  ]
}
```

**Note:** Panel information fields (`panelAmperageRating`, `panelVoltage`, `panelMaxKw`, `currentAmps`, `panelUtilizationPercent`) are included for US electrical panel-based VENs.

### Get Device Shadow

Returns current AWS IoT Device Shadow state (real-time snapshot).

```http
GET /api/vens/volttron_thing/shadow
```

**Response:**
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
          "current_kw": 2.1,
          "breaker_amps": 30,
          "critical": false
        }
      ],
      "active_event": {
        "event_id": "evt-abc123",
        "shed_kw": 5.0,
        "end_ts": 1729703600
      },
      "timestamp": 1729700000
    }
  }
}
```

---

The OpenAPI specification for these endpoints should mirror the models above. If maintained separately, ensure schema definitions for network statistics, VENs, loads, events, and time-series responses are kept in sync with this document.
