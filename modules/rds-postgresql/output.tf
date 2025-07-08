output "db_instance_endpoint" {
  value = aws_db_instance.this.endpoint
}

output "db_instance_identifier" {
  value = aws_db_instance.this.id
}