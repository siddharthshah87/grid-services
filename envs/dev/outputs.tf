# envs/dev/outputs.tf

output "alb_dns_name" {
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

output "volttron_service_name" {
  description = "ECS Service name for Volttron VEN"
  value       = module.ecs_service_volttron.name
}

