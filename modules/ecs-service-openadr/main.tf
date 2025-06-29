variable "name" {}
variable "cluster_id" {}
variable "subnet_ids" { type = list(string) }
variable "security_group_id" {}
variable "execution_role_arn" {}
variable "task_role_arn" {}
variable "image" {}
variable "mqtt_topic" {}
variable "mqtt_topic_metering" {}
variable "iot_endpoint" {}
variable "target_group_arn" {}
variable "cpu" { default = "256" }
variable "memory" { default = "512" }
variable "ca_cert_secret_arn" { default = null }
variable "client_cert_secret_arn" { default = null }
variable "private_key_secret_arn" { default = null }

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
        { name = "MQTT_TOPIC", value = var.mqtt_topic },
        { name = "MQTT_TOPIC_METERING", value = var.mqtt_topic_metering },
        { name = "IOT_ENDPOINT", value = var.iot_endpoint }
      ]
      secrets = concat(
        var.ca_cert_secret_arn != null ? [{ name = "CA_CERT", valueFrom = var.ca_cert_secret_arn }] : [],
        var.client_cert_secret_arn != null ? [{ name = "CLIENT_CERT", valueFrom = var.client_cert_secret_arn }] : [],
        var.private_key_secret_arn != null ? [{ name = "PRIVATE_KEY", valueFrom = var.private_key_secret_arn }] : []
      )
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
    assign_public_ip = true
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

