#!/bin/bash
CLUSTER_NAME="hems-ecs-cluster"

echo "🔧 Cleaning up ECS services from cluster: $CLUSTER_NAME"

for svc in openleadr-vtn volttron-ven; do
  echo "🔍 Checking $svc..."
  if aws ecs describe-services --cluster "$CLUSTER_NAME" --services "$svc" | grep -q '"status": "ACTIVE"'; then
    echo "➡️  Deleting $svc..."
    aws ecs delete-service --cluster "$CLUSTER_NAME" --service "$svc" --force
  else
    echo "✅ $svc not active or already deleted."
  fi
done

