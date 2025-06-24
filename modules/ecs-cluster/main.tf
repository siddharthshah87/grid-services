# modules/ecs-cluster/main.tf

resource "aws_ecs_cluster" "this" {
  name = var.name

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = var.tags
}

# Output for cluster ID
output "id" {
  value = aws_ecs_cluster.this.id
}

