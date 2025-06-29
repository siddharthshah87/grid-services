#!/bin/bash

set -euo pipefail

# Change this if your cluster name differs
CLUSTER_NAME="grid-services-cluster"

# Services to check and clean up
SERVICES=("volttron-ven" "openleadr-vtn")

echo "🔍 Checking ECS services in cluster: $CLUSTER_NAME"

for SERVICE in "${SERVICES[@]}"; do
  echo "🔎 Looking for service: $SERVICE"
  
  STATUS=$(aws ecs describe-services \
    --cluster "$CLUSTER_NAME" \
    --services "$SERVICE" \
    --query "services[0].status" \
    --output text 2>/dev/null || echo "MISSING")

  if [[ "$STATUS" == "ACTIVE" || "$STATUS" == "DRAINING" ]]; then
    echo "⚠️  Service $SERVICE exists in $STATUS state. Deleting..."
    aws ecs delete-service --cluster "$CLUSTER_NAME" --service "$SERVICE" --force
    echo "✅ Deleted ECS service: $SERVICE"
  else
    echo "✅ Service $SERVICE not found or already deleted."
  fi
done

echo "✅ ECS service cleanup complete."

