#!/bin/sh
set -e
alembic -c /app/alembic.ini upgrade head
exec "$@"
