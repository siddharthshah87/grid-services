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

module "ecs_cluster" {
  source = "../../modules/ecs-cluster"
  name   = "hems-ecs-cluster"
  tags = {
    Project = "grid-services"
  }
}

module "ecs_security_group" {
  source     = "../../modules/security-group"
  name       = "ecs-tasks-sg"
  vpc_id     = module.vpc.vpc_id
  allow_http = true
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
      name       = "CERT_BUNDLE_JSON"
      valueFrom = "arn:aws:secretsmanager:us-west-2:923675928909:secret:openleadr-iot-cert-bundle-oWaWux"
    }
  ]

  depends_on = [module.openadr_alb]
}

module "ecs_service_volttron" {
  source               = "../../modules/ecs-service-volttron"
  name                 = "volttron-ven"
  cluster_id           = module.ecs_cluster.id
  subnet_ids           = module.vpc.public_subnets
  security_group_id    = module.ecs_security_group.id
  execution_role_arn   = module.ecs_task_roles.execution
  task_role_arn        = module.ecs_task_roles.iot_mqtt
  image                = "${module.ecr_volttron.repository_url}:latest"
  mqtt_topic_events    = "oadr/event/ven1"
  mqtt_topic_responses = "oadr/response/ven1"
  mqtt_topic_metering  = "oadr/meter/ven1"
  mqtt_topic_status    = "ven/status/ven1"
  iot_endpoint         = module.iot_core.endpoint
}

