output "service_name" {
  value = aws_ecs_service.this.name
}

output "service_arn" {
  value = aws_ecs_service.this.id
}

output "log_group_name" {
  value = aws_cloudwatch_log_group.this.name
}
