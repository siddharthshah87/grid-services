#!/usr/bin/env bash
set -euo pipefail

# Run Terraform formatting check across the repository
terraform fmt -recursive -check

# Validate each environment under envs/
for env_dir in envs/*; do
  if [[ -d "$env_dir" ]]; then
    terraform validate "$env_dir"
  fi
done

echo "✅ Terraform formatting and validation passed."
