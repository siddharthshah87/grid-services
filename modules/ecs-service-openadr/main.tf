# modules/ecs-service-openadr/main.tf

variable "name" {}
variable "cluster_id" {}
variable "subnet_ids" { type = list(string) }
variable "security_group_id" {}
variable "execution_role_arn" {}
variable "task_role_arn" {}
variable "image" {}
variable "mqtt_topic" {}
variable "iot_endpoint" {}
variable "target_group_arn" {}
variable "cpu" { default = "256"}
variable "memory" {default = "512"}

resource "aws_ecs_task_definition" "this" {
  family                   = var.name
  network_mode            = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                     = "256"
  memory                  = "512"
  execution_role_arn      = var.execution_role_arn
  task_role_arn           = var.task_role_arn

  container_definitions = jsonencode([
    {
      name      = "${var.name}"
      image     = var.image
      essential = true
      portMappings = [
        {
          containerPort = 8080
          protocol       = "tcp"
        }
      ]
      environment = [
        { name = "MQTT_TOPIC", value = var.mqtt_topic },
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
    subnets         = var.subnet_ids
    security_groups = [var.security_group_id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = var.target_group_arn
    container_name   = var.name
    container_port   = 8080
  }

  desired_count = 1
}

output "name" {
  value = aws_ecs_service.this.name
}

