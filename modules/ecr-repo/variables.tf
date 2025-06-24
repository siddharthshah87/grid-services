variable "name" {
  description = "grid-services-ecr-repository"
  type        = string
}

variable "tags" {
  type    = map(string)
  default = {}
}

