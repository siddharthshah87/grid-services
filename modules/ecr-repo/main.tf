variable "name" {}

resource "aws_ecr_repository" "this" {
  name = var.name
  tags = var.tags
}

output "repository_url" {
  value = aws_ecr_repository.this.repository_url
}

