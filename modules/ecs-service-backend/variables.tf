variable "service_name" {}
variable "image" {}
variable "cluster_id" {}
variable "subnet_ids" {
  type = list(string)
}
variable "security_group_id" {}
variable "target_group_arn" {}
variable "assign_public_ip" { default = true }
variable "container_port" {
  default = 8000
}
variable "cpu" {
  default = 512
}
variable "memory" {
  default = 1024
}
variable "execution_role_arn" {}
variable "task_role_arn" {}
variable "aws_region" {
  default = "us-west-2"
}

variable "db_host" {
  type = string
}

variable "db_user" {
  type = string
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "db_name" {
  type = string
}

