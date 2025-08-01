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
variable "mqtt_topic_status" {}
variable "iot_endpoint" {}
variable "container_port" { default = 22916 }
variable "target_group_arn" { default = null }
variable "assign_public_ip" { default = true }
variable "cpu" { default = "256" }
variable "memory" { default = "512" }
variable "ca_cert_secret_arn" { default = null }
variable "client_cert_secret_arn" { default = null }
variable "private_key_secret_arn" { default = null }

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
      environment = [
        { name = "MQTT_TOPIC_EVENTS", value = var.mqtt_topic_events },
        { name = "MQTT_TOPIC_RESPONSES", value = var.mqtt_topic_responses },
        { name = "MQTT_TOPIC_METERING", value = var.mqtt_topic_metering },
        { name = "MQTT_TOPIC_STATUS", value = var.mqtt_topic_status },
        { name = "IOT_ENDPOINT", value = var.iot_endpoint }
      ]
      secrets = [
        {
          name      = "CA_CERT_PEM"
          valueFrom = "arn:aws:secretsmanager:us-west-2:923675928909:secret:ven-mqtt-certs:ca_cert::"
        },
        {
          name      = "CLIENT_CERT_PEM"
          valueFrom = "arn:aws:secretsmanager:us-west-2:923675928909:secret:ven-mqtt-certs:client_cert::"
        },
        {
          name      = "PRIVATE_KEY_PEM"
          valueFrom = "arn:aws:secretsmanager:us-west-2:923675928909:secret:ven-mqtt-certs:private_key::"
        }
      ]
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

  dynamic "load_balancer" {
    for_each = var.target_group_arn == null ? [] : [var.target_group_arn]
    content {
      target_group_arn = load_balancer.value
      container_name   = var.name
      container_port   = var.container_port
    }
  }

  desired_count = 1
  lifecycle {
    ignore_changes = [desired_count]
  }
}

output "name" {
  value = aws_ecs_service.this.name
}

output "log_group_name" {
  value = aws_cloudwatch_log_group.this.name
}
