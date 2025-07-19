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
- `DB_USER` – database user
- `DB_PASSWORD` – user's password
- `DB_NAME` – database name

The application connects on port `5432` by default.

### Authentication

Set the following variables to enable JWT authentication:

- `ADMIN_USERNAME` – username allowed to obtain tokens
- `ADMIN_PASSWORD_HASH` – bcrypt hash of the password
- `JWT_SECRET` – secret used to sign JWTs

Request a token by posting form data to `/login`:

```bash
curl -X POST -F 'username=<user>' -F 'password=<pass>' http://localhost:8000/login
```

Use the returned token in the `Authorization: Bearer` header when calling the
protected `/events` and `/devices` endpoints.

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
