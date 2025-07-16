#!/usr/bin/env bash
set -euo pipefail

: "${AWS_PROFILE?Must set AWS_PROFILE to your AWS profile name}"
CLUSTER_NAME="hems-ecs-cluster"
WORKSPACE="dev"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_DIR="$SCRIPT_DIR/../envs/$WORKSPACE"

echo "🚨 Starting full reset of ECS + Terraform environment [$WORKSPACE]"

### STEP 1: Delete ECS Services if Present ###
echo "🔧 Deleting ECS services if they exist..."
for svc in openleadr-vtn volttron-ven; do
  if aws ecs describe-services --cluster "$CLUSTER_NAME" --services "$svc" | grep -q '"status": "ACTIVE"'; then
    echo "➡️  Deleting $svc..."
    aws ecs update-service --cluster "$CLUSTER_NAME" --service "$svc" --desired-count 0
    sleep 3
    aws ecs delete-service --cluster "$CLUSTER_NAME" --service "$svc" --force
  else
    echo "✅ $svc not active or already deleted."
  fi
done

### STEP 2: Clean Up Terraform State ###
cd "$ENV_DIR"
echo "🧹 Cleaning stale Terraform state..."
terraform state list | grep 'module\.ecs_service_openadr\|module\.ecs_service_volttron\|module\.openadr_alb' | while read -r line; do
  terraform state rm "$line" || true
done

### STEP 3: Optional Re-import (uncomment if needed) ###
if [[ -f terraform_import.sh ]]; then
  echo "📦 Running terraform_import.sh to restore resource mappings..."
  ./terraform_import.sh
else
  echo "⚠️  Skipping import: terraform_import.sh not found"
fi

### STEP 4: Terraform Init + Apply ###
echo "🚀 Running terraform init and apply..."
./terraform_init.sh

echo "✅ Reset complete!"

