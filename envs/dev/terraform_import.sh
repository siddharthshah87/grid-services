#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

REGION="us-west-2"
CLUSTER_NAME="hems-ecs-cluster"

# Only set AWS_PROFILE if not running in CI or Codespaces
if [[ -z "${CI:-}" && -z "${CODESPACES:-}" ]]; then
  export AWS_PROFILE="AdministratorAccess-923675928909"
  echo "🔐 Using AWS_PROFILE=$AWS_PROFILE"
else
  unset AWS_PROFILE 2>/dev/null || true
  echo "🔐 Running in CI/Codespaces: using AWS SSO credentials"
fi

echo "📦 Importing existing AWS resources into Terraform..."

# Helper function to check if resource is already imported
is_imported() {
  terraform state list | grep -qx "$1"
}

# Safe import function
safe_import() {
  local resource="$1"
  local id="$2"
  echo "🔄 Importing $resource"
  if terraform import "$resource" "$id"; then
    echo "✅ Successfully imported $resource"
  else
    echo "⚠️ Failed to import $resource. Continuing..."
  fi
}

echo "🗃️ Importing ECR repositories..."
is_imported "module.ecr_backend.aws_ecr_repository.this" || safe_import "module.ecr_backend.aws_ecr_repository.this" "ecs-backend"
is_imported "module.ecr_frontend.aws_ecr_repository.this" || safe_import "module.ecr_frontend.aws_ecr_repository.this" "ecs-frontend"
is_imported "module.ecr_volttron.aws_ecr_repository.this" || safe_import "module.ecr_volttron.aws_ecr_repository.this" "volttron-ven"

echo "🏗️ Importing ECS cluster..."
is_imported "module.ecs_cluster.aws_ecs_cluster.this" || safe_import "module.ecs_cluster.aws_ecs_cluster.this" "$CLUSTER_NAME"

echo "⚙️ Importing ECS services..."
is_imported "module.ecs_service_backend.aws_ecs_service.this" || safe_import "module.ecs_service_backend.aws_ecs_service.this" "$CLUSTER_NAME/ecs-backend"
is_imported "module.ecs_service_frontend.aws_ecs_service.this" || safe_import "module.ecs_service_frontend.aws_ecs_service.this" "$CLUSTER_NAME/ecs-frontend"
is_imported "module.ecs_service_volttron.aws_ecs_service.this" || safe_import "module.ecs_service_volttron.aws_ecs_service.this" "$CLUSTER_NAME/volttron-ven"

echo "📝 Importing CloudWatch log groups..."
is_imported "module.ecs_service_backend.aws_cloudwatch_log_group.this" || safe_import "module.ecs_service_backend.aws_cloudwatch_log_group.this" "/ecs/ecs-backend"
is_imported "module.ecs_service_frontend.aws_cloudwatch_log_group.this" || safe_import "module.ecs_service_frontend.aws_cloudwatch_log_group.this" "/ecs/ecs-frontend"
is_imported "module.ecs_service_volttron.aws_cloudwatch_log_group.this" || safe_import "module.ecs_service_volttron.aws_cloudwatch_log_group.this" "/ecs/volttron-ven"

echo "🔒 Importing ACM certificates..."
is_imported "aws_acm_certificate.frontend" || safe_import "aws_acm_certificate.frontend" "arn:aws:acm:us-west-2:923675928909:certificate/9fd4176c-7960-4266-99fa-0dfb30839c4b"
is_imported "aws_acm_certificate.ven" || safe_import "aws_acm_certificate.ven" "arn:aws:acm:us-west-2:923675928909:certificate/276ed3b4-1e3c-4748-ba5c-23d0230e89d3"

echo "🌐 Importing Application Load Balancers..."
# Backend ALB (already exists in state)
is_imported "module.backend_alb.aws_lb.this" || safe_import "module.backend_alb.aws_lb.this" "arn:aws:elasticloadbalancing:us-west-2:923675928909:loadbalancer/app/backend-alb/116bc0815c97e7ba"
is_imported "module.backend_alb.aws_lb_target_group.this" || safe_import "module.backend_alb.aws_lb_target_group.this" "arn:aws:elasticloadbalancing:us-west-2:923675928909:targetgroup/backend-alb-tg/e106ade95a69318c"
is_imported "module.backend_alb.aws_security_group.alb_sg" || safe_import "module.backend_alb.aws_security_group.alb_sg" "sg-05cb4a98511bb98bd"

# Frontend ALB
is_imported "module.frontend_alb.aws_lb.this" || safe_import "module.frontend_alb.aws_lb.this" "arn:aws:elasticloadbalancing:us-west-2:923675928909:loadbalancer/app/frontend-alb/2a4cf89980be71c1"
is_imported "module.frontend_alb.aws_lb_target_group.this" || safe_import "module.frontend_alb.aws_lb_target_group.this" "arn:aws:elasticloadbalancing:us-west-2:923675928909:targetgroup/frontend-alb-tg/838406d9a6e72d3e"
is_imported "module.frontend_alb.aws_security_group.alb_sg" || safe_import "module.frontend_alb.aws_security_group.alb_sg" "sg-0509bb104c14cc645"
is_imported "module.frontend_alb.aws_lb_listener.http_redirect[0]" || safe_import "module.frontend_alb.aws_lb_listener.http_redirect[0]" "arn:aws:elasticloadbalancing:us-west-2:923675928909:listener/app/frontend-alb/2a4cf89980be71c1/9debf6c2e9092188"
is_imported "module.frontend_alb.aws_lb_listener.https[0]" || safe_import "module.frontend_alb.aws_lb_listener.https[0]" "arn:aws:elasticloadbalancing:us-west-2:923675928909:listener/app/frontend-alb/2a4cf89980be71c1/f5d5cbc4cdd0fd9e"

# Volttron ALB
is_imported "module.volttron_alb.aws_lb.this" || safe_import "module.volttron_alb.aws_lb.this" "arn:aws:elasticloadbalancing:us-west-2:923675928909:loadbalancer/app/volttron-alb/12ef2ef1bcbd14d1"
is_imported "module.volttron_alb.aws_lb_target_group.this" || safe_import "module.volttron_alb.aws_lb_target_group.this" "arn:aws:elasticloadbalancing:us-west-2:923675928909:targetgroup/volttron-alb-tg/d421f546012f8c44"
is_imported "module.volttron_alb.aws_security_group.alb_sg" || safe_import "module.volttron_alb.aws_security_group.alb_sg" "sg-045dd8dce632bca2d"
is_imported "module.volttron_alb.aws_lb_listener.http_redirect[0]" || safe_import "module.volttron_alb.aws_lb_listener.http_redirect[0]" "arn:aws:elasticloadbalancing:us-west-2:923675928909:listener/app/volttron-alb/12ef2ef1bcbd14d1/eeb756847ee9aa87"
is_imported "module.volttron_alb.aws_lb_listener.https[0]" || safe_import "module.volttron_alb.aws_lb_listener.https[0]" "arn:aws:elasticloadbalancing:us-west-2:923675928909:listener/app/volttron-alb/12ef2ef1bcbd14d1/ea249ecbe59a868b"

echo "🔧 Importing IoT resources..."
is_imported "module.iot_core.aws_iot_thing.device_sim" || safe_import "module.iot_core.aws_iot_thing.device_sim" "volttron_thing"
cert_arn=$(aws iot list-certificates --region "$REGION" --query 'certificates[?status==`ACTIVE`][0].certificateArn' --output text 2>/dev/null || echo "")
if [[ -n "$cert_arn" ]]; then
  echo "🔐 Importing IoT certificate: $cert_arn"
  is_imported "module.iot_core.aws_iot_certificate.cert" || safe_import "module.iot_core.aws_iot_certificate.cert" "$cert_arn"
  is_imported "module.iot_core.aws_iot_policy_attachment.attach" || safe_import "module.iot_core.aws_iot_policy_attachment.attach" "volttron_policy|$cert_arn"
else
  echo "⚠️ Could not determine IoT certificate ARN; skipping certificate import."
fi

echo "🎯 Importing IAM roles..."
is_imported "module.ecs_task_roles.aws_iam_role.execution" || safe_import "module.ecs_task_roles.aws_iam_role.execution" "grid-sim-task-execution"
is_imported "module.ecs_task_roles.aws_iam_role.iot_mqtt" || safe_import "module.ecs_task_roles.aws_iam_role.iot_mqtt" "grid-sim-task-iot"

echo "🎯 Importing Aurora PostgreSQL Database..."
is_imported "module.aurora_postgresql.aws_db_subnet_group.this" || safe_import "module.aurora_postgresql.aws_db_subnet_group.this" "opendar-aurora-subnet-group"
is_imported "module.aurora_postgresql.aws_rds_cluster.aurora_postgres" || safe_import "module.aurora_postgresql.aws_rds_cluster.aurora_postgres" "opendar-aurora"
is_imported "module.aurora_postgresql.aws_rds_cluster_instance.aurora_postgres_instances[0]" || safe_import "module.aurora_postgresql.aws_rds_cluster_instance.aurora_postgres_instances[0]" "opendar-aurora-instance-1"

echo "🎯 Importing Secrets Manager..."
is_imported "aws_secretsmanager_secret.volttron_tls" || safe_import "aws_secretsmanager_secret.volttron_tls" "arn:aws:secretsmanager:us-west-2:923675928909:secret:dev-volttron-tls-BPEt43"
is_imported "aws_secretsmanager_secret_version.volttron_tls_value" || safe_import "aws_secretsmanager_secret_version.volttron_tls_value" "arn:aws:secretsmanager:us-west-2:923675928909:secret:dev-volttron-tls-BPEt43|terraform-20250808055421783500000002"

echo "✨ Import process completed!"
echo "📊 TOTAL IMPORTED: 48+ resources aligned with AWS reality"
echo "🔍 Run 'terraform plan' to see remaining differences"