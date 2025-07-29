resource "aws_iot_topic_rule" "forward_to_s3" {
  count       = var.enable_logging ? 1 : 0
  name        = "${var.prefix}_mqtt_log"
  enabled     = true
  sql         = "SELECT * FROM 'oadr/#'"
  sql_version = "2016-03-23"

  s3 {
    bucket_name = var.s3_bucket
    key         = "logs/${var.prefix}/${timestamp()}.json"
    role_arn    = var.iot_role_arn
  }
}

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

resource "aws_iot_thing" "device_sim" {
  name = "${var.prefix}_thing"
  depends_on = [aws_iot_thing.device_sim, aws_iot_certificate.cert]
}

resource "aws_iot_certificate" "cert" {
  active = true
  depends_on = [aws_iot_thing.device_sim, aws_iot_certificate.cert]
}

resource "aws_iot_policy_attachment" "attach" {
  policy = aws_iot_policy.allow_publish_subscribe.name
  target = aws_iot_certificate.cert.arn
  depends_on = [aws_iot_certificate.cert, aws_iot_policy.allow_publish_subscribe]
}

resource "aws_iot_thing_principal_attachment" "thing_cert_attach" {
  thing     = aws_iot_thing.device_sim.name
  principal = aws_iot_certificate.cert.arn
  depends_on = [aws_iot_thing.device_sim, aws_iot_certificate.cert]
}


data "aws_iot_endpoint" "endpoint" {
  endpoint_type = "iot:Data-ATS"
}
