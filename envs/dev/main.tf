module "vpc" {
  source     = "../../modules/vpc"
  name       = "hems-demo-vpc"
  cidr_block = "10.10.0.0/16"
  az_count   = 2
  tags = {
    Project = "hems-demo"
    Env     = "dev"
  }
}

module "ecr_openleadr" {
  source = "../../modules/ecr-repo"
  name   = "openleadr-vtn"
  tags = {
    Project   = "grid-services"
    Component = "OpenADR"
  }
}

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
  name   = "ecs-tasks-sg"
  vpc_id = module.vpc.vpc_id
}

module "ecs_task_roles" {
  source      = "../../modules/iam-roles/ecs_task_roles"
  name_prefix = "grid-sim"
}

module "openadr_alb" {
  source            = "../../modules/alb"
  name              = "openadr-vtn-alb"
  vpc_id            = module.vpc.vpc_id
  public_subnets    = module.vpc.public_subnets
  listener_port     = 80
  target_port       = 8080
  health_check_path = "/health"
}
module "ecs_service_openadr" {
  source               = "../../modules/ecs-service-openadr"
  name                 = "openleadr-vtn"
  cluster_id           = module.ecs_cluster.id
  subnet_ids           = module.vpc.public_subnets
  security_group_id    = module.ecs_security_group.id
  execution_role_arn   = module.ecs_task_roles.execution
  task_role_arn        = module.ecs_task_roles.iot_mqtt
  image                = "${module.ecr_openleadr.repository_url}:latest"
  mqtt_topic_events    = "oadr/event/ven1"
  mqtt_topic_responses = "oadr/response/ven1"
  mqtt_topic_metering  = "oadr/meter/ven1"
  iot_endpoint         = module.iot_core.endpoint
  vens_port            = 8081
  target_group_arn     = module.openadr_alb.target_group_arn
  environment_secrets = [
    {
      name      = "CERT_BUNDLE_JSON"
      valueFrom = "arn:aws:secretsmanager:us-west-2:923675928909:secret:openleadr-iot-cert-bundle-oWaWux"
    }
  ]

  # Ensure the ECS service waits for the ALB listener and target group to be
  # created before attempting to register. This avoids race conditions during
  # provisioning.
  depends_on = [
    module.openadr_alb.listener,
    module.openadr_alb.target_group
  ]
}

module "ecs_service_volttron" {
  source                 = "../../modules/ecs-service-volttron"
  name                   = "volttron-ven"
  cluster_id             = module.ecs_cluster.id
  subnet_ids             = module.vpc.private_subnet_ids
  assign_public_ip       = false
  security_group_id      = module.ecs_security_group.id
  execution_role_arn     = module.ecs_task_roles.execution
  task_role_arn          = module.ecs_task_roles.iot_mqtt
  image                  = "${module.ecr_volttron.repository_url}:latest"
  mqtt_topic_events      = "oadr/event/ven1"
  mqtt_topic_responses   = "oadr/response/ven1"
  mqtt_topic_metering    = "oadr/meter/ven1"
  mqtt_topic_status      = "ven/status/ven1"
  iot_endpoint           = module.iot_core.endpoint
  ca_cert_secret_arn     = "arn:aws:secretsmanager:us-west-2:923675928909:secret:ven-mqtt-certs:ca_cert::"
  client_cert_secret_arn = "arn:aws:secretsmanager:us-west-2:923675928909:secret:ven-mqtt-certs:client_cert::"
  private_key_secret_arn = "arn:aws:secretsmanager:us-west-2:923675928909:secret:ven-mqtt-certs:private_key::"
  container_port         = 8000
  target_group_arn       = module.volttron_alb.target_group_arn

  # Wait for the ALB listener and target group before creating the service.
  depends_on = [
    module.volttron_alb.listener,
    module.volttron_alb.target_group
  ]
}

module "aurora_postgresql" {
  source             = "../../modules/rds-postgresql"
  name               = "opendar-aurora"
  db_name            = "openadrdb"
  engine_version     = "15.10"
  username           = "openadr_admin"
  password           = "Grid2025!" # Use Secrets Manager in production
  vpc_id             = module.vpc.vpc_id
  subnet_ids         = module.vpc.private_subnet_ids
  security_group_ids = [module.ecs_security_group.id]
  backup_retention   = 7
  db_instance_class  = "db.t4g.medium"
}

# Application load balancer for the backend service
module "backend_alb" {
  source            = "../../modules/alb"
  name              = "backend-alb"
  vpc_id            = module.vpc.vpc_id
  public_subnets    = module.vpc.public_subnets
  listener_port     = 80
  target_port       = 8000
  health_check_path = "/health"
}

module "volttron_alb" {
  source         = "../../modules/alb"
  name           = "volttron-alb"
  vpc_id         = module.vpc.vpc_id
  public_subnets = module.vpc.public_subnets
  # Expose the Volttron service publicly for easier debugging
  # by placing the ALB in the public subnets and making it
  # internet-facing. The default `internal` value is false
  # and `allowed_cidrs` defaults to ["0.0.0.0/0"].
  listener_port     = 80
  target_port       = 8000
  health_check_path = "/health"
}

# Ingress rules allowing traffic from the ALBs to the ECS tasks
resource "aws_security_group_rule" "ecs_from_backend_alb" {
  type                     = "ingress"
  from_port                = 8000
  to_port                  = 8000
  protocol                 = "tcp"
  security_group_id        = module.ecs_security_group.id
  source_security_group_id = module.backend_alb.security_group_id
}

resource "aws_security_group_rule" "ecs_from_openadr_alb" {
  type                     = "ingress"
  from_port                = 8080
  to_port                  = 8080
  protocol                 = "tcp"
  security_group_id        = module.ecs_security_group.id
  source_security_group_id = module.openadr_alb.security_group_id
}

resource "aws_security_group_rule" "ecs_from_volttron_alb" {
  count                    = var.enable_volttron_alb_rule ? 1 : 0
  type                     = "ingress"
  from_port                = var.volttron_port
  to_port                  = var.volttron_port
  protocol                 = "tcp"
  security_group_id        = module.ecs_security_group.id
  source_security_group_id = module.volttron_alb.security_group_id
}

resource "aws_security_group_rule" "ecs_postgresql" {
  type                     = "ingress"
  protocol                 = "tcp"
  from_port                = 5432
  to_port                  = 5432
  security_group_id        = module.ecs_security_group.id
  source_security_group_id = module.ecs_security_group.id
  description              = "PostgreSQL access from ECS tasks and Aurora"
}

resource "aws_security_group_rule" "ecs_egress_all" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = module.ecs_security_group.id
  description       = "Allow all egress"
}

module "ecr_backend" {
  source = "../../modules/ecr-repo"
  name   = "openadr-backend"
  tags = {
    Project   = "grid-services"
    Component = "Backend"
  }
}

module "ecs_service_backend" {
  source = "../../modules/ecs-service-backend"

  # -------- names ----------
  service_name = "openadr-backend"
  cluster_id   = module.ecs_cluster.id

  # -------- image ----------
  image = "${module.ecr_backend.repository_url}:latest"

  # place in public subnet *for now* so it can reach ECR
  subnet_ids        = module.vpc.public_subnets
  security_group_id = module.ecs_security_group.id
  target_group_arn  = module.backend_alb.target_group_arn

  # resources
  cpu            = 256
  memory         = 512
  container_port = 8000

  # roles
  execution_role_arn = module.ecs_task_roles.execution
  task_role_arn      = module.ecs_task_roles.iot_mqtt

  # DB connection env-vars
  db_host     = module.aurora_postgresql.db_host
  db_user     = module.aurora_postgresql.db_user
  db_password = module.aurora_postgresql.db_password
  db_name     = module.aurora_postgresql.db_name

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
  vpc_id            = module.vpc.vpc_id
  public_subnets    = module.vpc.public_subnets
  listener_port     = 80
  target_port       = 80
  health_check_path = "/"
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

  subnet_ids        = module.vpc.public_subnets
  security_group_id = module.ecs_security_group.id
  target_group_arn  = module.frontend_alb.target_group_arn

  cpu            = 256
  memory         = 512
  container_port = 80

  execution_role_arn = module.ecs_task_roles.execution
  task_role_arn      = module.ecs_task_roles.execution

  backend_api_url = "http://${module.backend_alb.dns_name}"
  aws_region      = var.aws_region
}
