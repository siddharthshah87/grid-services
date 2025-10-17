# VPC module disabled - using existing VPC vpc-0aab765c09cbb8f2b
# module "vpc" {
#   source     = "../../modules/vpc"
#   name       = "hems-demo-vpc"
#   cidr_block = "10.10.0.0/16"
#   az_count   = 2
#   tags = {
#     Project = "hems-demo"
#     Env     = "dev"
#   }
#   ecs_tasks_sg_id = module.ecs_security_group.id # ← here
# }

# Grid Event Gateway removed for cost optimization
# module "ecr_grid_event_gateway" {
#   source = "../../modules/ecr-repo"
#   name   = "grid-event-gateway"
#   tags = {
#     Project   = "grid-services"
#     Component = "OpenADR"
#   }
# }

module "ecr_volttron" {
  source = "../../modules/ecr-repo"
  name   = "volttron-ven"
  tags = {
    Project   = "grid-services"
    Component = "VOLTTRON"
  }
}

module "iot_core" {
  source         = "../../modules/iot-core"
  prefix         = "volttron"
  enable_logging = false
}

module "iot_rule_forwarder" {
  source           = "../../modules/iot-rule-forwarder"
  rule_name_prefix = "mqtt-forward"
  topics           = ["openadr/event", "volttron/metering"]
}

module "ecs_cluster" {
  source = "../../modules/ecs-cluster"
  name   = "hems-ecs-cluster"
  tags = {
    Project = "grid-services"
  }
}

module "ecs_security_group" {
  source = "../../modules/security-group"
  name   = "ecs-tasks"
  vpc_id = data.aws_vpc.existing.id
}

module "ecs_task_roles" {
  source                 = "../../modules/iam-roles/ecs_task_roles"
  name_prefix            = "grid-sim"
  tls_secret_arn         = aws_secretsmanager_secret.volttron_tls.arn
  additional_secret_arns = [aws_secretsmanager_secret.backend_tls.arn]
}

# Temporarily disabled Grid Event Gateway ALB to reduce costs
# module "grid_event_gateway_alb" {
#   source            = "../../modules/alb"
#   name              = "grid-event-gateway-alb"
#   vpc_id            = module.vpc.vpc_id
#   public_subnets    = module.vpc.public_subnets
#   listener_port     = 80
#   target_port       = 8080
#   health_check_path = "/health"
# }
# Temporarily disabled Grid Event Gateway to reduce costs
# module "ecs_service_grid_event_gateway" {
#   source               = "../../modules/ecs-service-openadr"
#   name                 = "grid-event-gateway"
#   cluster_id           = module.ecs_cluster.id
#   subnet_ids           = module.vpc.public_subnets
#   security_group_id    = module.ecs_security_group.id
#   execution_role_arn   = module.ecs_task_roles.execution
#   task_role_arn        = module.ecs_task_roles.iot_mqtt
#   image                = "${module.ecr_grid_event_gateway.repository_url}:latest"
#   mqtt_topic_events    = "oadr/event/ven1"
#   mqtt_topic_responses = "oadr/response/ven1"
#   mqtt_topic_metering  = "oadr/meter/ven1"
#   iot_endpoint         = module.iot_core.endpoint
#   iot_connect_host     = module.vpc.iot_data_endpoint_dns
#   iot_tls_server_name  = module.iot_core.endpoint
#   container_port       = 8080
#   vens_port            = 8081
#   target_group_arn     = module.grid_event_gateway_alb.target_group_arn
#   environment_secrets = [
#     {
#       name      = "CERT_BUNDLE_JSON"
#       valueFrom = "arn:aws:secretsmanager:us-west-2:923675928909:secret:grid-event-gateway-iot-cert-bundle-oWaWux"
#     }
#   ]
# 
#   # Ensure the ECS service waits for the ALB listener and target group to be
#   # created before attempting to register. This avoids race conditions during
#   # provisioning.
#   depends_on = [
#     module.grid_event_gateway_alb.listener,
#     module.grid_event_gateway_alb.target_group
#   ]
# }

# VEN now runs locally - no cloud infrastructure needed
# This saves costs and eliminates rc=7 MQTT disconnects from rolling deployments
# See volttron-ven/LOCAL_VEN.md for local setup instructions
#
# module "ecs_service_volttron" {
#   source                 = "../../modules/ecs-service-volttron"
#   name                   = "volttron-ven"
#   cluster_id             = module.ecs_cluster.id
#   subnet_ids             = data.aws_subnets.private.ids
#   assign_public_ip       = false
#   security_group_id      = module.ecs_security_group.id
#   execution_role_arn     = module.ecs_task_roles.execution
#   task_role_arn          = module.ecs_task_roles.iot_mqtt
#   image                  = "${module.ecr_volttron.repository_url}:latest"
#   mqtt_topic_events      = "oadr/event/ven1"
#   mqtt_topic_responses   = "oadr/response/ven1"
#   mqtt_topic_metering    = "volttron/metering"
#   mqtt_topic_status      = "ven/status/ven1"
#   iot_endpoint           = module.iot_core.endpoint
#   iot_connect_host       = data.aws_vpc_endpoint.iot_data.dns_entry[0].dns_name
#   iot_tls_server_name    = module.iot_core.endpoint
#   iot_thing_name         = module.iot_core.thing_name
#   ca_cert_secret_arn     = "${aws_secretsmanager_secret.volttron_tls.arn}:ca_cert::"
#   client_cert_secret_arn = "${aws_secretsmanager_secret.volttron_tls.arn}:client_cert::"
#   private_key_secret_arn = "${aws_secretsmanager_secret.volttron_tls.arn}:private_key::"
#   container_port         = 8000
#   target_group_arn       = module.volttron_alb.target_group_arn
#
#   # Wait for the ALB listener and target group before creating the service.
#   depends_on = [
#     module.volttron_alb.listener,
#     module.volttron_alb.target_group
#   ]
# }

module "aurora_postgresql" {
  source             = "../../modules/rds-postgresql"
  name               = "opendar-aurora"
  db_name            = "ecsbackenddb"
  engine_version     = "15.12" # Keep current version, can't downgrade
  username           = "ecs_backend_admin"
  password           = "Grid2025!" # Use Secrets Manager in production
  vpc_id             = data.aws_vpc.existing.id
  subnet_ids         = data.aws_subnets.private.ids
  security_group_ids = [module.ecs_security_group.id]
  backup_retention   = 1               # Reduced from 7 days for dev
  db_instance_class  = "db.t4g.medium" # Keep current class - micro not supported for 15.12
}

# Application load balancer for the backend service
module "backend_alb" {
  source            = "../../modules/alb"
  name              = "backend-alb"
  vpc_id            = data.aws_vpc.existing.id
  public_subnets    = data.aws_subnets.public.ids
  listener_port     = 80
  target_port       = 8000
  health_check_path = "/health"
}

# VEN ALB no longer needed - VEN runs locally
# module "volttron_alb" {
#   source         = "../../modules/alb"
#   name           = "volttron-alb"
#   vpc_id         = data.aws_vpc.existing.id
#   public_subnets = data.aws_subnets.public.ids
#   # Expose the Volttron service publicly for easier debugging
#   # by placing the ALB in the public subnets and making it
#   # internet-facing. The default `internal` value is false
#   # and `allowed_cidrs` defaults to ["0.0.0.0/0"].
#   listener_port     = 80
#   target_port       = 8000
#   health_check_path = "/health"
#   enable_https      = true
#   acm_cert_arn      = data.aws_acm_certificate.ven_validated.arn
# }

# Ingress rules allowing traffic from the ALBs to the ECS tasks
resource "aws_security_group_rule" "ecs_from_backend_alb" {
  type                     = "ingress"
  from_port                = 8000
  to_port                  = 8000
  protocol                 = "tcp"
  security_group_id        = module.ecs_security_group.id
  source_security_group_id = module.backend_alb.security_group_id
}

# Disabled with Grid Event Gateway service
# resource "aws_security_group_rule" "ecs_from_grid_event_gateway_alb" {
#   type                     = "ingress"
#   from_port                = 8080
#   to_port                  = 8080
#   protocol                 = "tcp"
#   security_group_id        = module.ecs_security_group.id
#   source_security_group_id = module.grid_event_gateway_alb.security_group_id
# }

# VEN security group rule no longer needed
# resource "aws_security_group_rule" "ecs_from_volttron_alb" {
#   count                    = var.enable_volttron_alb_rule ? 1 : 0
#   type                     = "ingress"
#   from_port                = var.volttron_port
#   to_port                  = var.volttron_port
#   protocol                 = "tcp"
#   security_group_id        = module.ecs_security_group.id
#   source_security_group_id = module.volttron_alb.security_group_id
# }

resource "aws_security_group_rule" "ecs_postgresql" {
  type                     = "ingress"
  protocol                 = "tcp"
  from_port                = 5432
  to_port                  = 5432
  security_group_id        = module.ecs_security_group.id
  source_security_group_id = module.ecs_security_group.id
  description              = "PostgreSQL access from ECS tasks and Aurora"
}

resource "aws_security_group_rule" "ecs_from_frontend_alb" {
  description              = "Allow Frontend ALB to ECS frontend tasks"
  type                     = "ingress"
  from_port                = 80
  to_port                  = 80
  protocol                 = "tcp"
  security_group_id        = module.ecs_security_group.id
  source_security_group_id = module.frontend_alb.security_group_id
}

# VPC endpoints security group rules - commented out since using existing VPC
# resource "aws_security_group_rule" "endpoints_443_from_ecs" {
#   type                     = "ingress"
#   from_port                = 443
#   to_port                  = 443
#   protocol                 = "tcp"
#   security_group_id        = module.vpc.vpc_endpoints_security_group_id
#   source_security_group_id = module.ecs_security_group.id
#   description              = "TLS (443) from ECS tasks"
# }

# 8883
# resource "aws_security_group_rule" "endpoints_8883_from_ecs" {
#   type                     = "ingress"
#   from_port                = 8883
#   to_port                  = 8883
#   protocol                 = "tcp"
#   security_group_id        = module.vpc.vpc_endpoints_security_group_id
#   source_security_group_id = module.ecs_security_group.id
#   description              = "TLS (8883) from ECS tasks for IoT"
# }

module "ecr_backend" {
  source = "../../modules/ecr-repo"
  name   = "ecs-backend"
  tags = {
    Project   = "grid-services"
    Component = "Backend"
  }
}

module "ecs_service_backend" {
  source = "../../modules/ecs-service-backend"

  # -------- names ----------
  service_name = "ecs-backend"
  cluster_id   = module.ecs_cluster.id

  # -------- image ----------
  image = "${module.ecr_backend.repository_url}:latest"

  # place in public subnet *for now* so it can reach ECR
  subnet_ids        = data.aws_subnets.public.ids
  security_group_id = module.ecs_security_group.id
  target_group_arn  = module.backend_alb.target_group_arn

  # resources - optimized for dev environment  
  cpu            = 256 # Valid Fargate combination
  memory         = 512 # Valid Fargate combination
  container_port = 8000

  # roles
  execution_role_arn = module.ecs_task_roles.execution
  task_role_arn      = module.ecs_task_roles.iot_mqtt

  # DB connection env-vars
  db_host     = module.aurora_postgresql.db_host
  db_user     = module.aurora_postgresql.db_user
  db_password = module.aurora_postgresql.db_password
  db_name     = module.aurora_postgresql.db_name

  # MQTT connection for VEN telemetry
  # TODO: Re-enable VPC endpoint once SNI configuration is fully tested
  # mqtt_host            = data.aws_vpc_endpoint.iot_data.dns_entry[0].dns_name
  # mqtt_tls_server_name = module.iot_core.endpoint
  mqtt_host            = module.iot_core.endpoint  # Temporarily use public endpoint

  # TLS certificates for AWS IoT Core authentication
  # Backend uses its own certificate (different from VOLTTRON VEN)
  ca_cert_secret_arn     = "${aws_secretsmanager_secret.backend_tls.arn}:ca_cert::"
  client_cert_secret_arn = "${aws_secretsmanager_secret.backend_tls.arn}:client_cert::"
  private_key_secret_arn = "${aws_secretsmanager_secret.backend_tls.arn}:private_key::"

  aws_region = var.aws_region

  depends_on = [
    # Ensure the backend ALB listener and target group exist before
    # creating the ECS service to avoid provisioning race conditions.
    module.backend_alb.listener,
    module.backend_alb.target_group,
    module.aurora_postgresql
  ]

}



# Application load balancer for the frontend service
module "frontend_alb" {
  source            = "../../modules/alb"
  name              = "frontend-alb"
  vpc_id            = data.aws_vpc.existing.id
  public_subnets    = data.aws_subnets.public.ids
  listener_port     = 80
  target_port       = 80
  health_check_path = "/health"
  enable_https      = true
  acm_cert_arn      = data.aws_acm_certificate.frontend_validated.arn
}

module "ecr_frontend" {
  source = "../../modules/ecr-repo"
  name   = "ecs-frontend"
  tags = {
    Project   = "grid-services"
    Component = "Frontend"
  }
}

module "ecs_service_frontend" {
  source = "../../modules/ecs-service-frontend"

  service_name = "ecs-frontend"
  cluster_id   = module.ecs_cluster.id
  image        = "${module.ecr_frontend.repository_url}:latest"

  subnet_ids        = data.aws_subnets.public.ids
  security_group_id = module.ecs_security_group.id
  target_group_arn  = module.frontend_alb.target_group_arn

  # resources - optimized for dev environment
  cpu            = 256 # Valid Fargate combination
  memory         = 512 # Valid Fargate combination
  container_port = 80

  execution_role_arn = module.ecs_task_roles.execution
  task_role_arn      = module.ecs_task_roles.execution

  backend_api_url = "http://${module.backend_alb.dns_name}"
  aws_region      = var.aws_region
}
