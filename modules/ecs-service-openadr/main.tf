#modules/ecs-service-openadr
variable "name" {}
variable "cluster_id" {}
variable "subnet_ids" { type = list(string) }
variable "security_group_id" {}
variable "execution_role_arn" {}
variable "task_role_arn" {}
variable "image" {}
variable "mqtt_topic_events" {}
variable "mqtt_topic_responses" {}
variable "mqtt_topic_metering" {}
variable "iot_endpoint" {}
variable "target_group_arn" {}
variable "assign_public_ip" { default = true }
variable "cpu" { default = "256" }
variable "memory" { default = "512" }
variable "vens_port" { default = 8081 }

data "aws_region" "current" {}

resource "aws_cloudwatch_log_group" "this" {
  name = "/ecs/${var.name}"
}

resource "aws_ecs_task_definition" "this" {
  family                   = var.name
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = var.execution_role_arn
  task_role_arn            = var.task_role_arn

  container_definitions = jsonencode([
    {
      name      = var.name
      image     = var.image
      essential = true
      portMappings = [
        {
          containerPort = 8080
          protocol      = "tcp"
        }
      ]
      environment = [
        { name = "MQTT_TOPIC_EVENTS", value = var.mqtt_topic_events },
        { name = "MQTT_TOPIC_RESPONSES", value = var.mqtt_topic_responses },
        { name = "MQTT_TOPIC_METERING", value = var.mqtt_topic_metering },
        { name = "IOT_ENDPOINT", value = var.iot_endpoint },
        { name = "VENS_PORT", value = tostring(var.vens_port) },
        { name = "DB_HOST", value = var.db_host },
        { name = "DB_USER", value = var.db_user },
        { name = "DB_PASSWORD", value = var.db_password },
        { name = "DB_NAME", value = var.db_name },
        { name = "RUN_MIGRATIONS_ON_STARTUP", value = tostring(var.run_migrations_on_startup) }
      ]
      secrets = var.environment_secrets
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.this.name
          awslogs-region        = data.aws_region.current.name
          awslogs-stream-prefix = var.name
        }
      }
    }
  ])
}

resource "aws_ecs_service" "this" {
  name            = var.name
  cluster         = var.cluster_id
  task_definition = aws_ecs_task_definition.this.arn
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.subnet_ids
    security_groups  = [var.security_group_id]
    assign_public_ip = var.assign_public_ip
  }

  load_balancer {
    target_group_arn = var.target_group_arn
    container_name   = var.name
    container_port   = 8080
  }

  desired_count = 1

  lifecycle {
    ignore_changes = [desired_count]
  }
}

output "name" {
  value = aws_ecs_service.this.name
}


