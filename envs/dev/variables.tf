variable "aws_region" {
  type    = string
  default = "us-west-2"
}

variable "db_password" {
  description = "Password for the OpenADR database"
  type        = string
  sensitive   = true
}
