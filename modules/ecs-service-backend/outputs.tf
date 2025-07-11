output "service_name" {
  value = aws_ecs_service.this.name
}
output "service_arn" {
  value = aws_ecs_service.this.id
}

output "log_group_name" {
  value = aws_cloudwatch_log_group.this.name
}

output "db_host" {
  value = var.db_host
}

output "db_user" {
  value = var.db_user
}

output "db_name" {
  value = var.db_name
}

output "db_password" {
  value     = var.db_password
  sensitive = true
}

