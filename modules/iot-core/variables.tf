variable "prefix" {
  description = "Prefix for all AWS IoT resources (e.g., 'volttron', 'openadr')"
  type        = string
}

variable "enable_logging" {
  description = "Whether to enable MQTT logging to S3"
  type        = bool
  default     = false
}

variable "iot_role_arn" {
  description = "IAM role ARN used by IoT rule to write to S3"
  type        = string
  default     = ""
}

variable "s3_bucket" {
  description = "Name of the S3 bucket to store MQTT logs"
  type        = string
  default     = ""
}
