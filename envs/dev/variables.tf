variable "aws_region" {
  type    = string
  default = "us-west-2"
}

variable "enable_volttron_alb_rule" {
  type    = bool
  default = true
}

variable "volttron_port" {
  type    = number
  default = 8000
}
