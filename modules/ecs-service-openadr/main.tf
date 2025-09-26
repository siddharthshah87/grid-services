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
variable "iot_connect_host" { default = null }
variable "iot_tls_server_name" { default = null }
variable "target_group_arn" {}
variable "assign_public_ip" { default = true }
variable "cpu" { default = "256" }
variable "memory" { default = "512" }
variable "container_port" { default = 8080 }
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
          containerPort = var.container_port
          hostPort      = var.container_port
          protocol      = "tcp"
        }
      ]
      environment = concat(
        [
          { name = "MQTT_TOPIC_EVENTS", value = var.mqtt_topic_events },
          { name = "MQTT_TOPIC_RESPONSES", value = var.mqtt_topic_responses },
          { name = "MQTT_TOPIC_METERING", value = var.mqtt_topic_metering },
          { name = "IOT_ENDPOINT", value = var.iot_endpoint },
          { name = "VENS_PORT", value = tostring(var.vens_port) }
        ],
        var.iot_connect_host == null ? [] : [
          { name = "IOT_CONNECT_HOST", value = var.iot_connect_host }
        ],
        var.iot_tls_server_name == null ? [] : [
          { name = "IOT_TLS_SERVER_NAME", value = var.iot_tls_server_name }
        ]
      )
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
    container_port   = var.container_port
  }

  desired_count = 1

  lifecycle {
    ignore_changes = [desired_count]
  }
}

output "name" {
  value = aws_ecs_service.this.name
}


