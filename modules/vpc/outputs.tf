# modules/vpc/outputs.tf
output "vpc_id" { value = aws_vpc.this.id }
output "public_subnets" { value = aws_subnet.public[*].id }
output "private_subnet_ids" { value = aws_subnet.private[*].id }
output "cidr_block" { value = var.cidr_block }
output "vpc_endpoints_security_group_id" {
  description = "SG that protects all interface endpoints"
  value       = aws_security_group.vpc_endpoints.id
}
output "iot_data_endpoint_dns" {
  description = "Private DNS name for the com.amazonaws.<region>.iot.data interface endpoint"
  # use the first (and only) DNS entry for the endpoint
  value = aws_vpc_endpoint.interface["iot.data"].dns_entry[0].dns_name
}
