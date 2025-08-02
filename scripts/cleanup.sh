#!/bin/bash

set -euo pipefail

echo "🔻 Starting cleanup of high-cost AWS infrastructure (ECS, ALB, IoT)..."

export AWS_PROFILE=AdministratorAccess-923675928909

# Optional safety check
read -p "⚠️  Are you sure you want to destroy ECS services and ALBs? (yes/no): " CONFIRM
if [[ "$CONFIRM" != "yes" ]]; then
  echo "❌ Cleanup cancelled."
  exit 1
fi

# Step 1: Stop and remove ECS services
echo "🧹 Destroying ECS services and tasks..."
terraform destroy \
  -target=module.ecs_service_grid_event_gateway \
  -target=module.ecs_service_volttron \
  -target=module.ecs_service_grid_event_gateway.aws_ecs_task_definition.this \
  -target=module.ecs_service_volttron.aws_ecs_task_definition.this \
  -auto-approve || true

# Step 2: Remove ALB (Application Load Balancer)
echo "🧹 Destroying ALB..."
terraform destroy \
  -target=module.grid_event_gateway_alb \
  -auto-approve || true

# Step 3: Remove IoT Core policies and rules
echo "🧹 Destroying IoT Core resources..."
terraform destroy \
  -target=module.iot_core \
  -auto-approve || true

echo "✅ Cleanup complete. Core infrastructure (VPC, ECR, IAM roles) is retained."

