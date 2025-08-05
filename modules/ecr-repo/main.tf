variable "name" {}

resource "aws_ecr_repository" "this" {
  name                 = var.name
  force_delete         = true      # allows deletion of repository even if it contains images
  image_tag_mutability = "MUTABLE" # or IMMUTABLE based on your needs
  tags                 = var.tags
}

output "repository_url" {
  value = aws_ecr_repository.this.repository_url
}

