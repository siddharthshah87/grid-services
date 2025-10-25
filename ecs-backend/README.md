# ECS Backend

This directory contains a FastAPI application providing the administration API for the Grid-Event Gateway.

## Setup

1. Install [Poetry](https://python-poetry.org/) and Python 3.11.
2. Install dependencies:
   ```bash
   poetry install
   ```
3. Set the required database environment variables.

### Required environment variables

The service loads its database settings from environment variables with the `DB_` prefix. Define the following variables or place them in a `.env` file:

- `DB_HOST` – hostname of the PostgreSQL server
- `DB_PORT` – port of the PostgreSQL server (default `5432`)
- `DB_USER` – database user
- `DB_PASSWORD` – user's password
- `DB_NAME` – database name
- `DB_TIMEOUT` – connection timeout in seconds (default `30`)

`DB_PORT` defaults to `5432` if unset.

### MQTT telemetry ingestion

When `MQTT_ENABLED=true` the FastAPI process starts an MQTT/AWS IoT Core consumer alongside the API server. The consumer subscribes to the VEN agent topics (`MQTT_TOPIC_METERING`, `MQTT_TOPIC_STATUS`, `BACKEND_LOADS_TOPIC`, plus any extra topics listed in `MQTT_TOPICS`) and persists telemetry and load snapshots using the application database session factory. Messages are parsed using the canonical VEN payload schema and stored in the `telemetry_readings`, `telemetry_loads`, and `load_snapshots` tables.

#### MQTT configuration variables

- `MQTT_ENABLED` – enable the consumer (`false` by default).
- `MQTT_HOST`/`MQTT_PORT` – broker endpoint and port (required when enabled).
- `MQTT_USE_TLS` – set to `false` for unsecured local brokers; defaults to `true`.
- `MQTT_CA_CERT`, `MQTT_CLIENT_CERT`, `MQTT_CLIENT_KEY` – filesystem paths to AWS IoT Core certificates. Mount the certificate directory into the container and reference the absolute paths here.
- `MQTT_USERNAME`/`MQTT_PASSWORD` – optional username/password for brokers that use basic auth.
- `MQTT_KEEPALIVE` – keepalive interval in seconds (default `60`).
- `MQTT_CLIENT_ID` – optional custom MQTT client identifier.
- `MQTT_TOPIC_METERING`, `MQTT_TOPIC_STATUS`, `MQTT_TOPIC_EVENTS`, `MQTT_TOPIC_RESPONSES` – topic overrides aligning with the VEN agent defaults.
- `BACKEND_LOADS_TOPIC` – topic carrying periodic load snapshots (disabled when unset).
- `MQTT_TOPICS` – comma-separated list of any additional topics that should be subscribed to alongside the defaults.

Operational notes:

- The consumer logs and skips invalid JSON payloads, but raises startup errors if a broker host/port is missing while enabled.
- AWS IoT Core deployments typically require TLS; mount certificates and set the path variables accordingly.
- Data persistence occurs on the same async SQLAlchemy session factory used by the API; commits happen per-message and will roll back automatically on failure.

## Running locally

Launch the API using Poetry:

```bash
poetry install
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Running with Docker

Build the image with the provided `Dockerfile` and pass the database settings when running:

```bash
docker build -t ecs-backend .
docker run -p 8000:8000 \
  -e DB_HOST=<db-host> \
  -e DB_USER=<db-user> \
  -e DB_PASSWORD=<db-password> \
  -e DB_NAME=<db-name> \
  ecs-backend
```

The container's entrypoint runs database migrations via Alembic before starting
the server. It now retries the upgrade a few times to handle cases where the
database is still coming online.

## Testing

Run the automated test suite (including MQTT consumer unit tests) with:

```bash
poetry run pytest
```

## API Overview

The service exposes REST endpoints to manage VENs and events. See `docs/backend-api.md` and `docs/backend-api.yaml` for full API details and models. Key endpoints include:

- `GET /api/stats/network` – network metrics
- `GET /api/vens` – list VENs
- `POST /api/vens` – create VEN
- `GET /api/vens/{ven_id}/events` – get event history for a VEN
- `GET /api/events` – list events
- `POST /api/events` – create event
- `DELETE /api/vens/{ven_id}` – remove VEN
- `DELETE /api/events/{event_id}` – remove event

### Example: Get VEN Event History

```bash
curl -X GET "http://backend-alb-948465488.us-west-2.elb.amazonaws.com/api/vens/volttron_thing/events"
```

This endpoint returns all DR event acknowledgments for the specified VEN, including detailed circuit curtailment information.

Refer to the API documentation for all supported endpoints, request/response formats, and data models.

## Database Migrations

Alembic is used for database migrations. Migrations run automatically on container startup. To manually run migrations:

```bash
poetry run alembic upgrade head
```

## Architecture & Dependencies

- FastAPI for REST API
- SQLAlchemy (async) for database access
- Alembic for migrations
- MQTT consumer for telemetry ingestion (optional)
- See `pyproject.toml` for all dependencies

## Environment Variables

See above for required DB and MQTT variables. Additional variables may be required for cloud deployment, logging, or secrets. Document any new variables in this README.

## Test Coverage

### Comprehensive Test Suite
The backend has extensive test coverage (105 tests, 100% passing):

**Test Categories**:
- **Router Tests** (`tests/test_routers_*.py`): API endpoint tests for VENs, events, stats, and health
- **Service Tests** (`tests/test_service_*.py`): Business logic for MQTT consumer, event dispatch, and heartbeat monitoring
- **Contract Tests** (`../tests/test_contract_*.py`): MQTT payload schema validation
- **Hypothesis Tests** (`tests/*_hypothesis.py`): Property-based tests for robust validation
- **Integration Tests** (`tests/test_circuit_history.py`, etc.): Full feature testing

To run all tests:
```bash
poetry run pytest
# OR with coverage:
PYTHONPATH=ecs-backend pytest --cov=app --cov-report=html
```

See `docs/test-status.md` for detailed test documentation.

Tests use `pytest`, `pytest-asyncio`, and `hypothesis` for comprehensive coverage. Add new tests for new endpoints, features, or bug fixes.

## Contributing

- Add docstrings and comments to new code.
- Update this README and API docs for new features.

## License
Specify license here.
