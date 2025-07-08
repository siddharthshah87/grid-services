output "cluster_endpoint" {
  value = aws_rds_cluster.aurora_postgres.endpoint
}

output "reader_endpoint" {
  value = aws_rds_cluster.aurora_postgres.reader_endpoint
}