#!/bin/sh
set -e
alembic -c /app/alembic upgrade head
exec "$@"
