resource "aws_secretsmanager_secret" "volttron_tls" {
  name        = "${var.prefix}-volttron-tls"
  description = "TLS credentials for VOLTTRON VEN from IoT module"
}

resource "aws_secretsmanager_secret_version" "volttron_tls_value" {
  secret_id = aws_secretsmanager_secret.volttron_tls.id
  secret_string = jsonencode({
    ca_cert     = file("${path.module}/../../modules/iot-core/ca.pem")
    client_cert = module.iot_core.certificate_pem
    private_key = module.iot_core.private_key
  })
}

resource "aws_secretsmanager_secret" "backend_tls" {
  name        = "${var.prefix}-backend-tls"
  description = "TLS credentials for Backend MQTT consumer from IoT module"
}

resource "aws_secretsmanager_secret_version" "backend_tls_value" {
  secret_id = aws_secretsmanager_secret.backend_tls.id
  secret_string = jsonencode({
    ca_cert     = file("${path.module}/../../modules/iot-core/ca.pem")
    client_cert = module.iot_core.backend_certificate_pem
    private_key = module.iot_core.backend_private_key
  })
}
