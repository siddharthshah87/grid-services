#!/usr/bin/env bash
set -euo pipefail

# Run Terraform formatting check across the repository
terraform fmt -recursive -check

# Validate each environment under envs/
for env_dir in envs/*; do
  if [[ -d "$env_dir" ]]; then
    echo "Validating $env_dir..."
    (cd "$env_dir" && terraform validate)
  fi
done

echo "✅ Terraform formatting and validation passed."
