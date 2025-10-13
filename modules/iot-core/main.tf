############################################################
#  MQTT → S3 log rule (optional)
############################################################
resource "aws_iot_topic_rule" "forward_to_s3" {
  count       = var.enable_logging ? 1 : 0
  name        = "${var.prefix}_mqtt_log"
  enabled     = true
  sql         = "SELECT * FROM 'oadr/#'"
  sql_version = "2016-03-23"

  s3 {
    bucket_name = var.s3_bucket
    # `${timestamp()}` is a valid IoT substitution token.
    key      = "logs/${var.prefix}/${timestamp()}.json"
    role_arn = var.iot_role_arn
  }
}

############################################################
#  Access policy
############################################################
resource "aws_iot_policy" "allow_publish_subscribe" {
  name = "${var.prefix}_policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "iot:Connect",
        "iot:Publish",
        "iot:Subscribe",
        "iot:Receive",
        "iot:GetThingShadow",
        "iot:UpdateThingShadow",
        "iot:DeleteThingShadow"
      ]
      Resource = "*"
    }]
  })
}

############################################################
#  Device identity
############################################################
resource "aws_iot_certificate" "volttron" {
  active = true

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_iot_certificate" "backend" {
  active = true

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_iot_thing" "volttron" {
  name = "${var.prefix}_thing"

  lifecycle {
    prevent_destroy = true
    ignore_changes  = [attributes]
  }
}

############################################################
#  Attachments (policy → cert, cert → thing)
############################################################
resource "aws_iot_policy_attachment" "cert_policy_volttron" {
  policy = aws_iot_policy.allow_publish_subscribe.name
  target = aws_iot_certificate.volttron.arn

  # Prevent the destroy-before-detach race:
  lifecycle {
    create_before_destroy = false
  }
}

resource "aws_iot_policy_attachment" "cert_policy_backend" {
  policy = aws_iot_policy.allow_publish_subscribe.name
  target = aws_iot_certificate.backend.arn

  # Prevent the destroy-before-detach race:
  lifecycle {
    create_before_destroy = false
  }
}

resource "aws_iot_thing_principal_attachment" "volttron" {
  thing     = aws_iot_thing.volttron.name
  principal = aws_iot_certificate.volttron.arn

  # Same ordering safeguard
  lifecycle {
    create_before_destroy = false
  }
}

############################################################
#  IoT data endpoint (output)
############################################################
data "aws_iot_endpoint" "endpoint" {
  endpoint_type = "iot:Data-ATS"
}

output "iot_endpoint" {
  value       = data.aws_iot_endpoint.endpoint.endpoint_address
  description = "Hostname for SDKs to publish/subscribe"
}
