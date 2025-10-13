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

variable "mqtt_host" {
  type        = string
  description = "MQTT broker hostname (AWS IoT Core endpoint)"
  default     = "a1mgxpe8mg484j-ats.iot.us-west-2.amazonaws.com"
}

variable "mqtt_tls_server_name" {
  type        = string
  description = "TLS SNI server name for certificate verification (IoT Core endpoint)"
  default     = null
}

variable "ca_cert_secret_arn" {
  type        = string
  description = "ARN of the CA certificate secret"
  default     = null
}

variable "client_cert_secret_arn" {
  type        = string
  description = "ARN of the client certificate secret"
  default     = null
}

variable "private_key_secret_arn" {
  type        = string
  description = "ARN of the private key secret"
  default     = null
}

