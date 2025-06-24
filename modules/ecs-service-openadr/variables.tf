variable "name" {}
variable "cluster_id" {}
variable "subnet_ids" { type = list(string) }
variable "security_group_id" {}
variable "execution_role_arn" {}
variable "task_role_arn" {}
variable "image" {}
variable "cpu" { default = 256 }
variable "memory" { default = 512 }
variable "target_group_arn" {}

variable "mqtt_topic" {}
variable "iot_endpoint" {}

