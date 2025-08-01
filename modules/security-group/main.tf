# modules/security-group/main.tf
variable "name" {}
variable "vpc_id" {}
resource "aws_security_group" "this" {
  name        = var.name
  description = "Security group for ECS tasks"
  vpc_id      = var.vpc_id

  ingress = []
  egress  = []

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
