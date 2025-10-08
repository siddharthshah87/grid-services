# ECS Backend

This directory contains a FastAPI application that powers the Grid-Event
Gateway administration API. The backend persists VEN telemetry, exposes
time-series statistics, and still serves a small set of in-memory fixtures used
by the UI while device provisioning flows are finalized.

## Setup

1. Install [Poetry](https://python-poetry.org/) and Python 3.11.
2. Install dependencies:
   ```bash
   poetry install
   ```
3. Provide database configuration through environment variables or a `.env`
   file.

### Required environment variables

The service loads its database settings from environment variables with the
`DB_` prefix. Define the following variables:

- `DB_HOST` – hostname of the PostgreSQL server
- `DB_PORT` – port of the PostgreSQL server (default `5432`)
- `DB_USER` – database user
- `DB_PASSWORD` – user's password
- `DB_NAME` – database name
- `DB_TIMEOUT` – connection timeout in seconds (default `30`)

`DB_PORT` defaults to `5432` if unset.

## Database schema and migrations

Telemetry from VEN MQTT payloads is stored in three Alembic-managed tables:

- `ven_telemetry` – panel-level readings for each VEN (`used_power_kw`,
  `shed_power_kw`, raw payload JSON, and timestamps).
- `ven_load_samples` – per-load readings emitted alongside telemetry, including
  load type, instantaneous usage, shed capability, and optional capacity
  estimates.
- `ven_statuses` – status transitions reported by VENs (e.g. `online`,
  `offline`) with optional structured details.

Run migrations locally after installing dependencies:

```bash
poetry run alembic upgrade head
```

The Docker entrypoint runs the same command on startup and retries while the
database is coming online.

## Running locally

Launch the API using Poetry:

```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Running with Docker

Build the image with the provided `Dockerfile` and pass the database settings
when running:

```bash
docker build -t ecs-backend .
docker run -p 8000:8000 \
  -e DB_HOST=<db-host> \
  -e DB_USER=<db-user> \
  -e DB_PASSWORD=<db-password> \
  -e DB_NAME=<db-name> \
  ecs-backend
```

## API Overview

The service currently supports three classes of endpoints:

1. **Telemetry-backed statistics** – `/api/stats/network`, `/api/stats/loads`,
   and `/api/stats/network/history` aggregate the persisted telemetry data to
   power the dashboard metrics and charts.
2. **VEN load insights** – `/api/vens/{venId}/loads`,
   `/api/vens/{venId}/loads/{loadId}`, `/api/vens/{venId}/history`, and
   `/api/vens/{venId}/loads/{loadId}/history` return the latest telemetry and
   historical samples for each VEN and load.
3. **Fixture-backed VEN and event management** – high-level VEN CRUD and ADR
   event endpoints still return the in-memory fixtures defined in
   `app/data/dummy.py`. These endpoints provide deterministic responses for the
   UI until full provisioning flows are wired up.

Refer to `docs/backend-api.md` and `docs/backend-api.yaml` for request/response
examples that align with the current implementation.
