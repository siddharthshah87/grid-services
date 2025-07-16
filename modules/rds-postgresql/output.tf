output "cluster_endpoint" {
  value = aws_rds_cluster.aurora_postgres.endpoint
}

output "reader_endpoint" {
  value = aws_rds_cluster.aurora_postgres.reader_endpoint
}

output "db_host" {
  value = aws_rds_cluster.aurora_postgres.endpoint
}

output "db_user" {
  value = var.username
}

output "db_password" {
  value     = var.password
  sensitive = true
}

output "db_name" {
  value = var.db_name
}

