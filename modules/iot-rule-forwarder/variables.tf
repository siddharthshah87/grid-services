variable "rule_name_prefix" {
  description = "Prefix used for the IoT rule and logging resources"
  type        = string
}

variable "topics" {
  description = "List of MQTT topic filters to capture"
  type        = list(string)
}
