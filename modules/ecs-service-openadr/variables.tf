variable "environment_secrets" {
  type    = list(object({ name = string, valueFrom = string }))
  default = []
}

