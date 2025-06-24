variable "prefix" {
  description = "Prefix for all MQTT/Iot resources"
  type        = string
}

variable "enable_logging" {
  description = "Enable MQTT logging rule"
  type        = bool
  default     = false
}

variable "iot_role_arn" {
  description = "IAM role ARN for IoT rule to use"
  type        = string
  default     = ""
}

variable "s3_bucket" {
  description = "S3 bucket name for MQTT logging"
  type        = string
  default     = ""
}

