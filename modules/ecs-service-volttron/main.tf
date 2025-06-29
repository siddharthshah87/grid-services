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
variable "cpu" { default = "256" }
variable "memory" { default = "512" }

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
      environment = [
        { name = "MQTT_TOPIC", value = var.mqtt_topic },
        { name = "MQTT_TOPIC_METERING", value = var.mqtt_topic_metering },
        { name = "IOT_ENDPOINT", value = var.iot_endpoint }
      ]
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

  desired_count = 1
  lifecycle {
    ignore_changes = [desired_count]
  }
}

output "name" {
  value = aws_ecs_service.this.name
}
