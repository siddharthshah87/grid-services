resource "aws_rds_cluster" "aurora_postgres" {
  cluster_identifier      = var.name
  engine                  = "aurora-postgresql"
  engine_version          = var.engine_version
  database_name           = var.db_name
  master_username         = var.username
  master_password         = var.password
  backup_retention_period = var.backup_retention
  db_subnet_group_name    = aws_db_subnet_group.this.name
  vpc_security_group_ids  = var.security_group_ids
  storage_encrypted       = true
  skip_final_snapshot     = true
}

resource "aws_rds_cluster_instance" "aurora_postgres_instances" {
  count               = var.instance_count
  identifier          = "${var.name}-instance-${count.index + 1}"
  cluster_identifier  = aws_rds_cluster.aurora_postgres.id
  instance_class      = var.db_instance_class
  engine              = aws_rds_cluster.aurora_postgres.engine
  engine_version      = aws_rds_cluster.aurora_postgres.engine_version
  publicly_accessible = var.publicly_accessible
}

resource "aws_db_subnet_group" "this" {
  name       = "${var.name}-subnet-group"
  subnet_ids = var.subnet_ids
}
