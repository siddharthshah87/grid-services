variable "name" {
  type        = string
  description = "Cluster name"
}

variable "db_name" {
  type        = string
  description = "Database name"
}

variable "username" {
  type        = string
  description = "Master username"
}

variable "password" {
  type        = string
  description = "Master password"
  sensitive   = true
}

variable "db_instance_class" {
  type        = string
  description = "Aurora instance type (e.g., db.serverless, db.r6g.large)"
}

variable "allocated_storage" {
  type        = number
  default     = 20
  description = "Ignored for Aurora, kept for compatibility"
}

variable "vpc_id" {
  type        = string
  description = "VPC ID"
}

variable "subnet_ids" {
  type        = list(string)
  description = "Private subnet IDs"
}

variable "security_group_ids" {
  type        = list(string)
  description = "Security group IDs for Aurora"
}

variable "backup_retention" {
  type        = number
  default     = 7
}

variable "publicly_accessible" {
  type        = bool
  default     = false
}

variable "engine_version" {
  type        = string
  default     = "15.4"
}

variable "instance_count" {
  type        = number
  default     = 1
}