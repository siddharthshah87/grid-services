variable "name" {
  type = string
}

variable "cidr_block" {
  type    = string
  default = "10.0.0.0/16"
}

variable "az_count" {
  type    = number
  default = 2
}

variable "tags" {
  type    = map(string)
  default = {}
}

variable "ecs_tasks_sg_id" {
  description = "Security-group ID of the ECS tasks"
  type        = string
}
