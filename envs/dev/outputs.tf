# envs/dev/outputs.tf

#output "grid_event_gateway_alb_dns_name" {
#  description = "Public DNS of the Grid-Event Gateway ALB"
#  value       = module.grid_event_gateway_alb.dns_name
#}

output "iot_endpoint" {
  description = "AWS IoT Core endpoint"
  value       = module.iot_core.endpoint
}

#output "grid_event_gateway_service_name" {
#  description = "ECS Service name for Grid-Event Gateway"
#  value       = module.ecs_service_grid_event_gateway.name
#}

#output "grid_event_gateway_log_group_name" {
#  description = "CloudWatch Log Group for Grid-Event Gateway"
#  value       = module.ecs_service_grid_event_gateway.log_group_name
#}

# VPC Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = data.aws_vpc.existing.id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = data.aws_subnets.private.ids
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = data.aws_subnets.public.ids
}

# ECS Cluster Outputs
output "ecs_cluster_id" {
  description = "ID of the ECS cluster"
  value       = module.ecs_cluster.id
}

# ALB Outputs - Backend
output "backend_alb_dns_name" {
  description = "DNS name of the backend load balancer"
  value       = module.backend_alb.dns_name
}

# ALB Outputs - Frontend
output "frontend_alb_dns_name" {
  description = "DNS name of the frontend load balancer"
  value       = module.frontend_alb.dns_name
}

# ALB Outputs - Volttron
output "volttron_alb_dns_name" {
  description = "DNS name of the volttron load balancer"
  value       = module.volttron_alb.dns_name
}

# Service Outputs
output "volttron_service_name" {
  description = "Name of the volttron ECS service"
  value       = module.ecs_service_volttron.name
}

# ECR Repository Outputs
output "ecr_backend_repository_url" {
  description = "URL of the backend ECR repository"
  value       = module.ecr_backend.repository_url
}

output "ecr_frontend_repository_url" {
  description = "URL of the frontend ECR repository"
  value       = module.ecr_frontend.repository_url
}

output "ecr_volttron_repository_url" {
  description = "URL of the volttron ECR repository"
  value       = module.ecr_volttron.repository_url
}

#output "ecr_grid_event_gateway_repository_url" {
#  description = "URL of the grid event gateway ECR repository"
#  value       = module.ecr_grid_event_gateway.repository_url
#}

