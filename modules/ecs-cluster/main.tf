# modules/ecs-cluster/main.tf

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

