#!/bin/bash

set -e

# Always run Terraform from the dev environment directory
cd "$(dirname "$0")/../envs/dev"

echo "🔻 Starting cleanup of high-cost AWS infrastructure (containers, ALB, IoT)..."

# Step 1: Stop and remove ECS services
echo "🧹 Destroying ECS services..."
terraform destroy \
  -target=module.ecs_service_openadr \
  -target=module.ecs_service_volttron \
  -auto-approve

# Step 2: Remove ALB (Application Load Balancer)
echo "🧹 Destroying ALB..."
terraform destroy \
  -target=module.openadr_alb \
  -auto-approve

# Step 3: Optionally remove IoT Core policies and rules
echo "🧹 Destroying IoT Core resources..."
terraform destroy \
  -target=module.iot_core \
  -auto-approve

echo "✅ Cleanup complete. Core infrastructure (VPC, ECR, IAM roles) is retained."

