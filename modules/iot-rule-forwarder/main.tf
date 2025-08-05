# modules/iot-rule-forwarder/main.tf

# S3 bucket for captured messages
resource "aws_s3_bucket" "log_bucket" {
  bucket        = "${var.rule_name_prefix}-mqtt-logs"
  force_destroy = true
}

# Kinesis stream for realtime processing
resource "aws_kinesis_stream" "log_stream" {
  name        = "${var.rule_name_prefix}-mqtt-stream"
  shard_count = 1
}

# IAM role allowing IoT to write to the destinations
resource "aws_iam_role" "rule_role" {
  name = "${var.rule_name_prefix}-iot-rule-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Principal = { Service = "iot.amazonaws.com" },
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "actions" {
  name = "${var.rule_name_prefix}-iot-rule-policy"
  role = aws_iam_role.rule_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = ["s3:PutObject"],
        Resource = "${aws_s3_bucket.log_bucket.arn}/*"
      },
      {
        Effect   = "Allow",
        Action   = ["kinesis:PutRecord"],
        Resource = aws_kinesis_stream.log_stream.arn
      }
    ]
  })
}


# IoT rules for each topic
resource "aws_iot_topic_rule" "forward_rules" {
  for_each = toset(var.topics)
  # IoT rule names only allow alphanumeric characters and underscores. Replace
  # any disallowed characters in the prefix and topic filter to ensure
  # validation succeeds.
  name        = "${replace(var.rule_name_prefix, "-", "_")}_${replace(each.key, "/", "_")}"
  enabled     = true
  sql         = "SELECT * FROM '${each.key}'"
  sql_version = "2016-03-23"

  s3 {
    bucket_name = aws_s3_bucket.log_bucket.id
    key         = "${replace(each.key, "/", "_")}/${timestamp()}.json"
    role_arn    = aws_iam_role.rule_role.arn
  }

  kinesis {
    role_arn      = aws_iam_role.rule_role.arn
    stream_name   = aws_kinesis_stream.log_stream.name
    partition_key = "iot"
  }

  lifecycle {
    # Ignore the dynamically-generated S3 key so Terraform stops trying to update it
    ignore_changes = [s3]
  }
}

