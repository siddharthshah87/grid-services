#!/usr/bin/env bash
set -euo pipefail

echo "🧨 Tearing down the development environment..."

cd "$(dirname "$0")"

./scripts/cleanup.sh

echo "🧹 Environment teardown complete."

