# Region must match the ALB (yours is us-west-2)
provider "aws" {
  region = var.aws_region
}

data "aws_route53_zone" "gridcircuit" {
  name = "gridcircuit.link."
}

resource "aws_acm_certificate" "frontend" {
  domain_name       = "app.gridcircuit.link"
  validation_method = "DNS"
}

resource "aws_route53_record" "frontend_cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.frontend.domain_validation_options :
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

resource "aws_acm_certificate_validation" "frontend" {
  certificate_arn         = aws_acm_certificate.frontend.arn
  validation_record_fqdns = [for r in aws_route53_record.frontend_cert_validation : r.fqdn]
}


# Route53 alias (app host → ALB)
resource "aws_route53_record" "app_alias" {
  zone_id = data.aws_route53_zone.gridcircuit.zone_id
  name    = "app.gridcircuit.link"
  type    = "A"
  alias {
    name                   = module.frontend_alb.dns_name
    zone_id                = module.frontend_alb.lb_zone_id
    evaluate_target_health = false
  }
}

