# modules/security-group/main.tf
variable "name" {}
variable "vpc_id" {}
variable "allow_http" {
  type    = bool
  default = true
}


resource "aws_security_group" "this" {
  name        = var.name
  description = "Security group for ECS tasks"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    self        = true
    description = "PostgreSQL access from ECS tasks and Aurora"
  }

  dynamic "ingress" {
    for_each = var.allow_http ? [1] : []
    content {
      from_port   = 8080
      to_port     = 8080
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = var.name
  }
}


output "id" {
  value = aws_security_group.this.id
}
