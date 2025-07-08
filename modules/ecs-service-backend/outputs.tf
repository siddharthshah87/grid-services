output "service_name" {
  value = aws_ecs_service.this.name
}
output "service_arn" {
  value = aws_ecs_service.this.arn
}

output "db_host" {
  value = aws_rds_cluster.aurora_postgres.endpoint
}

output "db_user" {
  value = aws_rds_cluster.aurora_postgres.username
}

output "db_name" {
  value = aws_rds_cluster.aurora_postgres.db_name
}

output "db_password" {
  value = var.password
  sensitive = true
}

