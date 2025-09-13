# Backend API Design

This document summarizes backend API endpoints required to support the Smart Grid Control Center dashboard and future load insights.

## Data Model

- **NetworkStats** – summary metrics such as `venCount`, `controllablePowerKw`, `potentialLoadReductionKw`, `efficiencyPercent`, and `householdUsageKw`.
- **VEN** – a Virtual End Node with `id`, `name`, `status`, `location {lat, lon}`, `loads[]`, and `metrics` describing current power and shed availability.
- **Load** – device attached to a VEN with `id`, `type`, `capacityKw`, `shedCapabilityKw`, and `currentPowerKw`.
- **Event** – ADR event with `id`, `status`, `startTime`, `endTime`, `requestedReductionKw`, and `actualReductionKw`.
- **TimeseriesPoint** – `{timestamp, powerKw}` used in historical responses.

## Network Statistics

- `GET /stats/network` – current network metrics (VEN counts, controllable power, load reduction, efficiency, household usage).
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
  "efficiencyPercent": 95.2,
  "householdUsageKw": 890
}
```

## VEN Management

- `GET /vens` – list registered Virtual End Nodes including status, power data, and coordinates for mapping.
- `POST /vens` – register a new VEN.
- `GET /vens/{venId}` – fetch detailed VEN information.
- `PATCH /vens/{venId}` – update VEN configuration.
- `DELETE /vens/{venId}` – remove a VEN.
- `GET /vens/{venId}/loads` – list controllable loads attached to a VEN.
- `GET /vens/{venId}/loads/{loadId}` – detailed load data (capacity, shed capability, current power).
- `PATCH /vens/{venId}/loads/{loadId}` – update load metadata or configuration.
- `POST /vens/{venId}/loads/{loadId}/commands/shed` – issue a shed command for a specific load.
- `GET /vens/{venId}/history` – historical metrics for a VEN.
- `GET /vens/{venId}/loads/{loadId}/history` – historical power data for a specific load.

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
  "metrics": { "currentPowerKw": 12.4, "shedAvailabilityKw": 5.0 }
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
  "requestedReductionKw": 500
}
```

## Historical Queries

- `GET /stats/network/history` – network level history.
- `GET /vens/{venId}/history` – VEN level history.
- `GET /vens/{venId}/loads/{loadId}/history` – load level history.

### Example

```http
GET /vens/ven-123/history?start=2024-07-10T15:00:00Z&end=2024-07-10T17:00:00Z&granularity=5m
```

```json
{
  "points": [
    { "timestamp": "2024-07-10T15:00:00Z", "powerKw": 5.2 },
    { "timestamp": "2024-07-10T15:05:00Z", "powerKw": 5.0 }
  ]
}
```

The accompanying `backend-api.yaml` file provides the formal Swagger/OpenAPI specification for these endpoints, including schema definitions for network statistics, VENs, loads, events, and historical time-series responses.

