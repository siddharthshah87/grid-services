# modules/security-group/main.tf
variable "name" {}
variable "vpc_id" {}
resource "aws_security_group" "this" {
  name        = var.name
  description = "Security group for ECS tasks"
  vpc_id      = var.vpc_id

  #default outbound rules so terraform stops trying to delete AWS's implicit egress
  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    ipv6_cidr_blocks = []
    prefix_list_ids = []
    security_groups = []
    self = false
  }

  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name = var.name
  }
}


output "id" {
  value = aws_security_group.this.id
}

