# modules/ecs-cluster/main.tf

variable "name" {
  description = "Name of the ECS cluster"
  type        = string
}

variable "tags" {
  description = "Tags to apply to the ECS cluster"
  type        = map(string)
  default     = {}
}

resource "aws_ecs_cluster" "this" {
  name = var.name

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = var.tags
}

output "id" {
  description = "ID of the ECS cluster"
  value       = aws_ecs_cluster.this.id
}

