#!/usr/bin/env bash
set -euo pipefail
export AWS_PROFILE=AdministratorAccess-923675928909
REGION=us-west-2
CLUSTER=hems-ecs-cluster

echo "▶️  Scaling ECS services to 0"
for svc in openleadr-vtn volttron-ven openadr-backend ecs_frontend; do
  aws ecs update-service --cluster "$CLUSTER" --service "$svc" \
       --desired-count 0 --region "$REGION"
done

echo "🛑 Stopping Aurora cluster"
aws rds stop-db-cluster --db-cluster-identifier opendar-aurora --region "$REGION"

echo "💸 Deleting ALBs (they recreate quickly via Terraform)"
terraform destroy \
  -target=module.openadr_alb \
  -target=module.backend_alb \
  -auto-approve

echo "✅ Dev environment parked – running cost now ≈ \$0"

