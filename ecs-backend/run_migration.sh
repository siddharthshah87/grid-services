#!/bin/bash
# Run Alembic migrations with required environment variables
#
# Usage: ./run_migration.sh
#
# Set your database credentials before running:
# - If using local database, set DB_* variables below
# - If using AWS RDS, get credentials from Terraform outputs

set -e

# Database configuration (update these for your environment)
export DB_HOST="${DB_HOST:-localhost}"
export DB_PORT="${DB_PORT:-5432}"
export DB_USER="${DB_USER:-postgres}"
export DB_PASSWORD="${DB_PASSWORD:-postgres}"
export DB_NAME="${DB_NAME:-grid_services}"

# Optional: MQTT settings (not required for migration)
export MQTT_ENABLED="${MQTT_ENABLED:-false}"

# IoT settings (not required for migration)
export EVENT_COMMAND_ENABLED="${EVENT_COMMAND_ENABLED:-false}"

echo "Running Alembic migration..."
echo "Database: postgresql://${DB_USER}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
echo ""

cd "$(dirname "$0")"
PYTHONPATH="$(pwd):$PYTHONPATH" alembic upgrade head

echo ""
echo "✅ Migration complete!"
