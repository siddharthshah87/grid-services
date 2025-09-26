resource "aws_acm_certificate" "ven" {
  domain_name       = "sim.gridcircuit.link"
  validation_method = "DNS"
}

resource "aws_route53_record" "ven_cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.ven.domain_validation_options :
    dvo.domain_name => {
      name  = dvo.resource_record_name
      type  = dvo.resource_record_type
      value = dvo.resource_record_value
    }
  }
  zone_id = data.aws_route53_zone.gridcircuit.zone_id
  name    = each.value.name
  type    = each.value.type
  records = [each.value.value]
  ttl     = 60
}

resource "aws_acm_certificate_validation" "ven" {
  certificate_arn         = aws_acm_certificate.ven.arn
  validation_record_fqdns = [for r in aws_route53_record.ven_cert_validation : r.fqdn]
}
