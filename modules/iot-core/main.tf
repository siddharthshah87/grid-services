resource "aws_iot_policy" "allow_publish_subscribe" {
  name = "${var.prefix}_policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "iot:Connect",
          "iot:Publish",
          "iot:Subscribe",
          "iot:Receive"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iot_certificate" "cert" {
  active = true
}

resource "aws_iot_thing" "device_sim" {
  name = "${var.prefix}_thing"
}

resource "aws_iot_policy_attachment" "attach" {
  policy = aws_iot_policy.allow_publish_subscribe.name
  target = aws_iot_certificate.cert.arn

  depends_on = [
    aws_iot_certificate.cert,
    aws_iot_policy.allow_publish_subscribe
  ]
}

resource "aws_iot_thing_principal_attachment" "thing_cert_attach" {
  thing     = aws_iot_thing.device_sim.name
  principal = aws_iot_certificate.cert.arn

  depends_on = [
    aws_iot_certificate.cert,
    aws_iot_thing.device_sim
  ]
}

# 🔐 Helps Terraform destroy attachments first before cert/thing
resource "null_resource" "detach_ordering" {
  depends_on = [
    aws_iot_thing_principal_attachment.thing_cert_attach,
    aws_iot_policy_attachment.attach
  ]
}
