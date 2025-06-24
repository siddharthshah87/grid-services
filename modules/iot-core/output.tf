output "thing_name" {
  value = aws_iot_thing.device_sim.name
}

output "certificate_pem" {
  value = aws_iot_certificate.cert.certificate_pem
}

output "private_key" {
  value = aws_iot_certificate.cert.private_key
}

output "public_key" {
  value = aws_iot_certificate.cert.public_key
}

output "policy_name" {
  value = aws_iot_policy.allow_publish_subscribe.name
}


output "endpoint" {
  value = data.aws_iot_endpoint.this.endpoint
}

