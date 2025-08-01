# envs/dev/outputs.tf

output "openleadr_alb_dns_name" {
  description = "Public DNS of the OpenADR ALB"
  value       = module.openadr_alb.dns_name
}

output "iot_endpoint" {
  description = "AWS IoT Core endpoint"
  value       = module.iot_core.endpoint
}

output "openleadr_service_name" {
  description = "ECS Service name for OpenADR VTN"
  value       = module.ecs_service_openadr.name
}

output "openleadr_log_group_name" {
  description = "CloudWatch Log Group for OpenADR"
  value       = module.ecs_service_openadr.log_group_name
}

output "volttron_service_name" {
  description = "ECS Service name for Volttron VEN"
  value       = module.ecs_service_volttron.name
}

output "volttron_log_group_name" {
  description = "CloudWatch Log Group for Volttron"
  value       = module.ecs_service_volttron.log_group_name
}

# DNS name for the backend ALB
output "backend_alb_dns_name" {
  description = "Public DNS of the backend ALB"
  value       = module.backend_alb.dns_name
}

# DNS name for the frontend ALB
output "frontend_alb_dns_name" {
  description = "Public DNS of the frontend ALB"
  value       = module.frontend_alb.dns_name
}

