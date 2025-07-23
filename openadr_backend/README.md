# OpenADR Backend

This directory contains a FastAPI application providing the administration API for the OpenADR VTN.

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

## Running locally

Launch the API using Poetry:

```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Running with Docker

Build the image with the provided `Dockerfile` and pass the database settings when running:

```bash
docker build -t openadr-backend .
docker run -p 8000:8000 \
  -e DB_HOST=<db-host> \
  -e DB_USER=<db-user> \
  -e DB_PASSWORD=<db-password> \
  -e DB_NAME=<db-name> \
  openadr-backend
```

The container's entrypoint runs database migrations via Alembic before starting
the server. It now retries the upgrade a few times to handle cases where the
database is still coming online.
