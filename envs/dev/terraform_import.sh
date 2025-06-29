#!/usr/bin/env bash
set -euo pipefail

export AWS_PROFILE=AdministratorAccess-923675928909
REGION="us-west-2"

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

echo "✅ All necessary resources imported or already managed."

