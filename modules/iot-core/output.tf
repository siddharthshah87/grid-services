output "thing_name" {
  value = aws_iot_thing.volttron.name
}

output "certificate_pem" {
  value = aws_iot_certificate.volttron.certificate_pem
}

output "private_key" {
  value = aws_iot_certificate.volttron.private_key
}

output "public_key" {
  value = aws_iot_certificate.volttron.public_key
}

output "backend_certificate_pem" {
  value = aws_iot_certificate.backend.certificate_pem
}

output "backend_private_key" {
  value = aws_iot_certificate.backend.private_key
}

output "backend_public_key" {
  value = aws_iot_certificate.backend.public_key
}

output "policy_name" {
  value = aws_iot_policy.allow_publish_subscribe.name
}

output "endpoint" {
  value = data.aws_iot_endpoint.endpoint.endpoint_address
}

