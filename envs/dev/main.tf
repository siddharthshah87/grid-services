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
  source                   = "../../modules/security-group"
  name                     = "ecs-tasks-sg"
  vpc_id                   = module.vpc.vpc_id
  allow_http               = false
  alb_backend_sg_id        = module.backend_alb.security_group_id
  alb_vtn_sg_id            = module.openadr_alb.security_group_id
  alb_volttron_sg_id       = module.volttron_alb.security_group_id
  enable_alb_volttron_rule = true
  volttron_port            = 8000
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

  depends_on = [module.openadr_alb]
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

  subnet_ids        = module.vpc.private_subnet_ids
  assign_public_ip  = false
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
    module.backend_alb,
    module.aurora_postgresql
  ]
}

