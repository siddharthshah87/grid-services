variable "service_name" {}
variable "image" {}
variable "cluster_id" {}
variable "subnet_ids" { type = list(string) }
variable "security_group_id" {}
variable "target_group_arn" {}
variable "container_port" { default = 80 }
variable "cpu" { default = 256 }
variable "memory" { default = 512 }
variable "execution_role_arn" {}
variable "task_role_arn" {}
variable "aws_region" { default = "us-west-2" }
variable "backend_api_url" {}
