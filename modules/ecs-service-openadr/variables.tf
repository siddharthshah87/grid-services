variable "environment_secrets" {
  type    = list(object({ name = string, valueFrom = string }))
  default = []
}

variable "db_host" {
  type    = string
  default = ""
}

variable "db_user" {
  type    = string
  default = ""
}

variable "db_password" {
  type      = string
  sensitive = true
  default   = ""
}

variable "db_name" {
  type    = string
  default = ""
}

variable "run_migrations_on_startup" {
  type    = bool
  default = true
}

