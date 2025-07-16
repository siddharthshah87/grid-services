output "log_bucket_name" {
  value = aws_s3_bucket.log_bucket.bucket
}

output "log_stream_name" {
  value = aws_kinesis_stream.log_stream.name
}

output "rule_names" {
  value = [for r in aws_iot_topic_rule.forward_rules : r.name]
}
