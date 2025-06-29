#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Bringing up the full development environment..."

cd "$(dirname "$0")/envs/dev"

# Optional: Re-import resources if needed (only run this if your state was wiped)
./terraform_import.sh

# Initialize and apply the infra
./terraform_init.sh

echo "✅ Environment is up. All services should be running."

