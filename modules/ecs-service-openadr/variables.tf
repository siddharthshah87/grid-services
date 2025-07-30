variable "environment_secrets" {
  type    = list(object({ name = string, valueFrom = string }))
  default = []
}

variable "run_migrations_on_startup" {
  type    = bool
  default = true
}

