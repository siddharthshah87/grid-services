#!/bin/sh
set -e

# Retry migrations a few times in case the database is still starting up
MAX_TRIES=${MAX_TRIES:-5}
TRY=1
until alembic -c /app/alembic.ini upgrade head; do
    if [ "$TRY" -ge "$MAX_TRIES" ]; then
        echo "Failed to run migrations after $TRY attempts" >&2
        exit 1
    fi
    echo "Alembic failed to reach $DB_HOST:$DB_PORT (attempt $TRY/$MAX_TRIES), retrying in 5s" >&2
    TRY=$((TRY + 1))
    sleep 5
done

exec "$@"
