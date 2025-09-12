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

variable "frontend_cert_arn" {
  description = "ACM certificate ARN for the frontend ALB"
  type        = string
  default     = null
}

variable "prefix" {
  type    = string
  default = "dev"
}
