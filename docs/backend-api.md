# Backend API Design

This document summarizes backend API endpoints required to support the Smart Grid Control Center dashboard and future load insights.

## Data Model

- **NetworkStats** – summary metrics such as `venCount`, `controllablePowerKw`, `potentialLoadReductionKw`, and `householdUsageKw`. This shall give overall status of the VEN network. These data are expected to be aggregated in the backend returned here for overview data.
- **VEN** – a Virtual End Node with `id`, `name`, `status`, `location {lat, lon}`, `loads[]`, and `metrics` describing current power, shed availability, and Shed status (ADR event id, shed load's ids)
- **Load** – device attached to a VEN with `id`, `type`, `capacityKw`, `shedCapabilityKw`, and `currentPowerKw`.
- **Event** – ADR event with `id`, `status`, `startTime`, `endTime`, (`requestedReductionKw`, and `actualReductionKw` -- need to confirm if openADR specifies)
- **TimeseriesPoint** – VEN level and system level `{timestamp, used powerKw, shed powerKw(what was requested and id)}` used in historical responses.

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

- `GET /vens` – list registered Virtual End Nodes including `id`, `name`, `status`, `location` (lat, lon), `loads[]`, and `metrics` (see below) for mapping and quick stats.
- `POST /vens` – register a new VEN.
- `GET /vens/{venId}` – fetch detailed VEN information.
- `PATCH /vens/{venId}` – update VEN configuration.
- `DELETE /vens/{venId}` – remove a VEN.
- `GET /vens/{venId}/loads` – list controllable loads attached to a VEN.
- `GET /vens/{venId}/loads/{loadId}` – detailed load data with fields `capacityKw`, `shedCapabilityKw`, and `currentPowerKw`.
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

The OpenAPI specification for these endpoints should mirror the models above. If maintained separately, ensure schema definitions for network statistics, VENs, loads, events, and time-series responses are kept in sync with this document.
