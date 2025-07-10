#!/usr/bin/env bash
set -euo pipefail

export AWS_PROFILE=AdministratorAccess-923675928909
REGION="us-west-2"
CLUSTER_NAME="hems-ecs-cluster"

echo "📦 Importing existing AWS resources into Terraform..."

# Helper function to check if resource is already imported
is_imported() {
  terraform state list | grep -q "$1"
}

### ECR Repos
echo "🗃️  Importing ECR repositories..."
if ! is_imported "module.ecr_openleadr.aws_ecr_repository.this"; then
  terraform import module.ecr_openleadr.aws_ecr_repository.this openleadr-vtn
else
  echo "✅ openleadr-vtn already imported"
fi

if ! is_imported "module.ecr_volttron.aws_ecr_repository.this"; then
  terraform import module.ecr_volttron.aws_ecr_repository.this volttron-ven
else
  echo "✅ volttron-ven already imported"
fi

### IAM Roles
echo "🔐 Importing IAM roles..."
if ! is_imported "module.ecs_task_roles.aws_iam_role.execution"; then
  terraform import module.ecs_task_roles.aws_iam_role.execution grid-sim-task-execution
else
  echo "✅ execution role already imported"
fi

if ! is_imported "module.ecs_task_roles.aws_iam_role.iot_mqtt"; then
  terraform import module.ecs_task_roles.aws_iam_role.iot_mqtt grid-sim-task-iot
else
  echo "✅ iot_mqtt role already imported"
fi

### IoT Core Policy
echo "🔗 Importing IoT policy..."
if ! is_imported "module.iot_core.aws_iot_policy.allow_publish_subscribe"; then
  terraform import module.iot_core.aws_iot_policy.allow_publish_subscribe volttron_policy
else
  echo "✅ IoT policy already imported"
fi

### ALB and Target Group
echo "🌐 Fetching ALB and target group ARNs..."
alb_arn=$(aws elbv2 describe-load-balancers \
  --names openadr-vtn-alb \
  --region $REGION \
  --query "LoadBalancers[0].LoadBalancerArn" \
  --output text || echo "")

tg_arn=$(aws elbv2 describe-target-groups \
  --names openadr-vtn-alb-tg \
  --region $REGION \
  --query "TargetGroups[0].TargetGroupArn" \
  --output text || echo "")

if [[ -z "$alb_arn" || -z "$tg_arn" ]]; then
  echo "❌ Failed to fetch ALB or Target Group ARN. Aborting."
  exit 1
fi

echo "🌍 Importing ALB: $alb_arn"
if ! is_imported "module.openadr_alb.aws_lb.this"; then
  terraform import module.openadr_alb.aws_lb.this "$alb_arn"
else
  echo "✅ ALB already imported"
fi

echo "🎯 Importing Target Group: $tg_arn"
if ! is_imported "module.openadr_alb.aws_lb_target_group.this"; then
  terraform import module.openadr_alb.aws_lb_target_group.this "$tg_arn"
else
  echo "✅ Target Group already imported"
fi

### Backend ALB and Target Group
echo "🌐 Fetching Backend ALB and target group ARNs..."
backend_alb_arn=$(aws elbv2 describe-load-balancers \
  --names backend-alb \
  --region $REGION \
  --query "LoadBalancers[0].LoadBalancerArn" \
  --output text || echo "")

backend_tg_arn=$(aws elbv2 describe-target-groups \
  --names backend-alb-tg \
  --region $REGION \
  --query "TargetGroups[0].TargetGroupArn" \
  --output text || echo "")

if [[ -z "$backend_alb_arn" || -z "$backend_tg_arn" ]]; then
  echo "❌ Failed to fetch Backend ALB or Target Group ARN. Aborting."
  exit 1
fi

echo "🌍 Importing Backend ALB: $backend_alb_arn"
if ! is_imported "module.backend_alb.aws_lb.this"; then
  terraform import module.backend_alb.aws_lb.this "$backend_alb_arn"
else
  echo "✅ Backend ALB already imported"
fi

echo "🎯 Importing Backend Target Group: $backend_tg_arn"
if ! is_imported "module.backend_alb.aws_lb_target_group.this"; then
  terraform import module.backend_alb.aws_lb_target_group.this "$backend_tg_arn"
else
  echo "✅ Backend Target Group already imported"
fi

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
      echo "❌ Could not find a task definition for $family_name"
      return
    fi
    echo "📦 Importing task definition: $arn"
    terraform import "$module_path" "$arn"
  else
    echo "✅ $family_name task definition already imported"
  fi
}

import_task_definition "module.ecs_service_openadr.aws_ecs_task_definition.this" "openleadr-vtn"
import_task_definition "module.ecs_service_volttron.aws_ecs_task_definition.this" "volttron-ven"
import_task_definition "module.ecs_service_backend.aws_ecs_task_definition.this" "openadr-backend"

### ALB Security groups
echo "🛡️  Importing ALB security group..."
alb_sg_id=$(aws ec2 describe-security-groups \
  --filters Name=group-name,Values=openadr-vtn-alb-sg \
  --region "$REGION" \
  --query "SecurityGroups[0].GroupId" \
  --output text 2>/dev/null || echo "")

if [[ -n "$alb_sg_id" ]] && ! is_imported "module.openadr_alb.aws_security_group.alb_sg"; then
  terraform import module.openadr_alb.aws_security_group.alb_sg "$alb_sg_id"
else
  echo "✅ ALB security group already imported or not found"
fi

backend_alb_sg_id=$(aws ec2 describe-security-groups \
  --filters Name=group-name,Values=backend-alb-sg \
  --region "$REGION" \
  --query "SecurityGroups[0].GroupId" \
  --output text 2>/dev/null || echo "")

if [[ -n "$backend_alb_sg_id" ]] && ! is_imported "module.backend_alb.aws_security_group.alb_sg"; then
  terraform import module.backend_alb.aws_security_group.alb_sg "$backend_alb_sg_id"
else
  echo "✅ Backend ALB security group already imported or not found"
fi

### ECS Services
echo "🧩 Importing ECS services..."

if aws ecs describe-services --cluster "$CLUSTER_NAME" --services openleadr-vtn --region "$REGION" \
  | grep -q "\"status\": \"ACTIVE\""; then
  if ! is_imported "module.ecs_service_openadr.aws_ecs_service.this"; then
    terraform import module.ecs_service_openadr.aws_ecs_service.this "${CLUSTER_NAME}/openleadr-vtn"
  else
    echo "✅ openleadr ECS service already imported"
  fi
else
  echo "⚠️  openleadr-vtn service not found or inactive"
fi

if aws ecs describe-services --cluster "$CLUSTER_NAME" --services volttron-ven --region "$REGION" \
  | grep -q "\"status\": \"ACTIVE\""; then
  if ! is_imported "module.ecs_service_volttron.aws_ecs_service.this"; then
    terraform import module.ecs_service_volttron.aws_ecs_service.this "${CLUSTER_NAME}/volttron-ven"
  else
    echo "✅ volttron ECS service already imported"
  fi
else
  echo "⚠️  volttron-ven service not found or inactive"
fi

if aws ecs describe-services --cluster "$CLUSTER_NAME" --services openadr-backend --region "$REGION" \
  | grep -q "\"status\": \"ACTIVE\""; then
  if ! is_imported "module.ecs_service_backend.aws_ecs_service.this"; then
    terraform import module.ecs_service_backend.aws_ecs_service.this "${CLUSTER_NAME}/openadr-backend"
  else
    echo "✅ openadr-backend ECS service already imported"
  fi
else
  echo "⚠️  openadr-backend service not found or inactive"
fi


echo "✅ All necessary resources imported or already managed."

