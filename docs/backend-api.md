# Backend API Guide

The ECS backend is a FastAPI service that exposes telemetry, statistics, and
fixture-backed administration endpoints for the Grid-Event Gateway UI. This
reference focuses on the REST surface that is currently implemented in
`ecs-backend/app/routers`.

## Data persistence overview

Incoming VEN MQTT payloads (documented in `docs/ven-contract.md`) are persisted
into three PostgreSQL tables managed by Alembic:

- **`ven_telemetry`** – panel-level metrics for each VEN, including
  `used_power_kw`, `shed_power_kw`, the raw payload JSON, and a timestamp.
- **`ven_load_samples`** – per-load snapshots attached to telemetry payloads. A
  row captures `load_id`, optional `load_type`, instantaneous usage, shed
  capability, and any supplemental metadata provided by the VEN.
- **`ven_statuses`** – status transitions (e.g. `online`, `offline`) with
  structured details and timestamps for the most recent heartbeat.

`crud.py` contains the query helpers that power the API responses by selecting
and aggregating data from these tables.

## Telemetry-backed statistics

`/api/stats` aggregates the latest samples to drive the dashboard summary cards
and charts.

- `GET /stats/network` – returns a `NetworkStats` object summarising the most
  recent telemetry per VEN. In addition to core metrics (`venCount`,
  `controllablePowerKw`, `potentialLoadReductionKw`, `householdUsageKw`), the
  response includes optional UI-only fields such as `onlineVens` and
  `averageHousePower` when they can be derived from the data.
- `GET /stats/loads` – groups the latest `ven_load_samples` by `load_type` and
  reports totals for `totalCapacityKw`, `totalShedCapabilityKw`, and
  `currentUsageKw`.
- `GET /stats/network/history` – streams historical network usage. The endpoint
  accepts optional `start`, `end`, and `granularity` query parameters
  (granularity defaults to `5m`). Results are bucketed into
  `HistoryResponse.points`, each containing `timestamp`, `usedPowerKw`, and
  `shedPowerKw` values.

### Example – network history

```http
GET /api/stats/network/history?start=2024-07-10T15:00:00Z&end=2024-07-10T17:00:00Z&granularity=15m
```

```json
{
  "points": [
    { "timestamp": "2024-07-10T15:00:00+00:00", "usedPowerKw": 12.31, "shedPowerKw": 2.45 },
    { "timestamp": "2024-07-10T15:15:00+00:00", "usedPowerKw": 11.08, "shedPowerKw": 1.92 }
  ]
}
```

## VEN telemetry and loads

Telemetry persistence enables per-VEN and per-load drill-downs:

- `GET /vens/{venId}/loads` – returns the latest sample for each load associated
  with the VEN. Each load includes instantaneous power, shed capability, and any
  optional fields that were reported (capacity, type, name, etc.).
- `GET /vens/{venId}/loads/{loadId}` – retrieves the most recent sample for a
  specific load.
- `GET /vens/{venId}/history` – returns aggregated panel-level history for the
  VEN using the same query parameters as `/stats/network/history`.
- `GET /vens/{venId}/loads/{loadId}/history` – returns historical samples for a
  specific load.

Each history endpoint defaults to the full range of stored data when `start` and
`end` are omitted.

## Fixture-backed administration endpoints

High-level VEN CRUD and ADR event endpoints (`/api/vens`, `/api/events`, and
related sub-routes) currently expose deterministic fixtures defined in
`app/data/dummy.py`. They provide predictable responses for the frontend while
provisioning workflows are still being implemented. When replacing the fixtures
with database-backed records, keep the documented response shapes stable.

## OpenAPI reference

`docs/backend-api.yaml` mirrors the behaviour described above and can be used to
import the API into Postman or other tooling. Regenerate or update the spec when
new endpoints are added or existing ones change.
