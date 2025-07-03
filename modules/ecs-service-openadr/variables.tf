variable "environment_secrets" {
  type    = list(object({ name = string, value_from = string }))
  default = []
}

