#!/bin/bash

set -euo pipefail

CLUSTER_NAME="grid-services-cluster"
SERVICES=("volttron-ven" "openleadr-vtn")

echo "🔧 Cleaning up stale ECS services (if any)..."

for SERVICE in "${SERVICES[@]}"; do
  STATUS=$(aws ecs describe-services \
    --cluster "$CLUSTER_NAME" \
    --services "$SERVICE" \
    --query "services[0].status" \
    --output text 2>/dev/null || echo "MISSING")

  if [[ "$STATUS" == "ACTIVE" || "$STATUS" == "DRAINING" ]]; then
    echo "⚠️  Found existing ECS service: $SERVICE. Deleting..."
    aws ecs delete-service --cluster "$CLUSTER_NAME" --service "$SERVICE" --force
    echo "✅ Deleted ECS service: $SERVICE"
  else
    echo "✅ ECS service $SERVICE not found or already removed."
  fi
done

echo "🔍 Verifying security groups..."
SEC_GROUP_ID=$(aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=openleadr-vtn-sg" \
  --query "SecurityGroups[0].GroupId" \
  --output text 2>/dev/null || echo "MISSING")

if [[ "$SEC_GROUP_ID" == "MISSING" || "$SEC_GROUP_ID" == "None" ]]; then
  echo "🚨 ERROR: Required security group 'openleadr-vtn-sg' not found. Please ensure it exists."
  exit 1
else
  echo "✅ Found security group: $SEC_GROUP_ID"
fi

echo "🚀 Running Terraform apply"
terraform apply -auto-approve

