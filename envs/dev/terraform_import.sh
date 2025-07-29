#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

REGION="us-west-2"
CLUSTER_NAME="hems-ecs-cluster"

# Only set AWS_PROFILE if not running in CI
if [[ -z "${CI:-}" ]]; then
  export AWS_PROFILE="AdministratorAccess-923675928909"
  echo "🔐 Using AWS_PROFILE=$AWS_PROFILE"
else
  unset AWS_PROFILE
  echo "🔐 Running in CI: using AWS OIDC credentials"
fi

echo "📦 Importing existing AWS resources into Terraform..."

# Helper function to check if resource is already imported
is_imported() {
  terraform state list | grep -qx "$1"
}

# Safe import wrapper
safe_import() {
  local addr=$1
  local id=$2
  if ! terraform import "$addr" "$id"; then
    echo "⚠️ Failed to import $addr. Continuing..."
  fi
}

### ECR Repos
echo "🗃️  Importing ECR repositories..."
is_imported "module.ecr_openleadr.aws_ecr_repository.this" || safe_import "module.ecr_openleadr.aws_ecr_repository.this" "openleadr-vtn"
is_imported "module.ecr_volttron.aws_ecr_repository.this" || safe_import "module.ecr_volttron.aws_ecr_repository.this" "volttron-ven"
is_imported "module.ecr_backend.aws_ecr_repository.this"   || safe_import "module.ecr_backend.aws_ecr_repository.this"   "openadr-backend"

### IAM Roles
echo "🔐 Importing IAM roles..."
is_imported "module.ecs_task_roles.aws_iam_role.execution" || safe_import "module.ecs_task_roles.aws_iam_role.execution" "grid-sim-task-execution"
is_imported "module.ecs_task_roles.aws_iam_role.iot_mqtt"  || safe_import "module.ecs_task_roles.aws_iam_role.iot_mqtt"  "grid-sim-task-iot"

### IoT Policy
echo "🔗 Importing IoT policy..."
is_imported "module.iot_core.aws_iot_policy.allow_publish_subscribe" || safe_import "module.iot_core.aws_iot_policy.allow_publish_subscribe" "volttron_policy"

### ALB and Target Group
echo "🌐 Fetching ALB and target group ARNs..."
alb_arn=$(aws elbv2 describe-load-balancers --names openadr-vtn-alb --region "$REGION" --query "LoadBalancers[0].LoadBalancerArn" --output text || echo "")
tg_arn=$(aws elbv2 describe-target-groups --names openadr-vtn-alb-tg --region "$REGION" --query "TargetGroups[0].TargetGroupArn" --output text || echo "")

if [[ -z "$alb_arn" || -z "$tg_arn" ]]; then
  echo "❌ Failed to fetch ALB or Target Group ARN. Aborting."
  exit 1
fi

echo "🌍 Importing ALB: $alb_arn"
is_imported "module.openadr_alb.aws_lb.this" || safe_import "module.openadr_alb.aws_lb.this" "$alb_arn"

echo "🎯 Importing Target Group: $tg_arn"
is_imported "module.openadr_alb.aws_lb_target_group.this" || safe_import "module.openadr_alb.aws_lb_target_group.this" "$tg_arn"

### Backend ALB and Target Group
echo "🌐 Fetching Backend ALB and target group ARNs..."
backend_alb_arn=$(aws elbv2 describe-load-balancers --names backend-alb --region "$REGION" --query "LoadBalancers[0].LoadBalancerArn" --output text || echo "")
backend_tg_arn=$(aws elbv2 describe-target-groups --names backend-alb-tg --region "$REGION" --query "TargetGroups[0].TargetGroupArn" --output text || echo "")

if [[ -z "$backend_alb_arn" || -z "$backend_tg_arn" ]]; then
  echo "❌ Failed to fetch Backend ALB or Target Group ARN. Aborting."
  exit 1
fi

echo "🌍 Importing Backend ALB: $backend_alb_arn"
is_imported "module.backend_alb.aws_lb.this" || safe_import "module.backend_alb.aws_lb.this" "$backend_alb_arn"

echo "🎯 Importing Backend Target Group: $backend_tg_arn"
is_imported "module.backend_alb.aws_lb_target_group.this" || safe_import "module.backend_alb.aws_lb_target_group.this" "$backend_tg_arn"

### ECS Task Definitions
echo "🚀 Importing ECS task definitions..."

get_latest_task_def_arn() {
  local family=$1
  aws ecs list-task-definitions \
    --family-prefix "$family" \
    --sort DESC \
    --region "$REGION" \
    --query 'taskDefinitionArns[0]' \
    --output text
}

import_task_definition() {
  local module_path=$1
  local family_name=$2
  if ! is_imported "$module_path"; then
    local arn
    arn=$(get_latest_task_def_arn "$family_name")
    if [[ "$arn" == "None" || -z "$arn" ]]; then
      echo "❌ No task definition found for $family_name"
      return
    fi
    safe_import "$module_path" "$arn"
  else
    echo "✅ $family_name task definition already imported"
  fi
}

import_task_definition "module.ecs_service_openadr.aws_ecs_task_definition.this" "openleadr-vtn"
import_task_definition "module.ecs_service_volttron.aws_ecs_task_definition.this" "volttron-ven"
import_task_definition "module.ecs_service_backend.aws_ecs_task_definition.this" "openadr-backend"

### ALB Security groups
echo "🛡️  Importing ALB security groups..."
alb_sg_id=$(aws ec2 describe-security-groups --filters Name=group-name,Values=openadr-vtn-alb-sg --region "$REGION" --query "SecurityGroups[0].GroupId" --output text 2>/dev/null || echo "")
[[ -n "$alb_sg_id" ]] && is_imported "module.openadr_alb.aws_security_group.alb_sg" || safe_import "module.openadr_alb.aws_security_group.alb_sg" "$alb_sg_id"

backend_alb_sg_id=$(aws ec2 describe-security-groups --filters Name=group-name,Values=backend-alb-sg --region "$REGION" --query "SecurityGroups[0].GroupId" --output text 2>/dev/null || echo "")
[[ -n "$backend_alb_sg_id" ]] && is_imported "module.backend_alb.aws_security_group.alb_sg" || safe_import "module.backend_alb.aws_security_group.alb_sg" "$backend_alb_sg_id"

### ECS Services
echo "🧩 Importing ECS services..."

import_service() {
  local name=$1
  local tf_path=$2
  if aws ecs describe-services --cluster "$CLUSTER_NAME" --services "$name" --region "$REGION" | grep -q "\"status\": \"ACTIVE\""; then
    is_imported "$tf_path" || safe_import "$tf_path" "${CLUSTER_NAME}/${name}"
  else
    echo "⚠️  $name service not found or inactive"
  fi
}

import_service "openleadr-vtn" "module.ecs_service_openadr.aws_ecs_service.this"
import_service "volttron-ven" "module.ecs_service_volttron.aws_ecs_service.this"
import_service "openadr-backend" "module.ecs_service_backend.aws_ecs_service.this"

echo "✅ All necessary resources imported or already managed."
