# Certificate already exists - imported
# resource "aws_acm_certificate" "ven" {
#   domain_name       = "sim.gridcircuit.link"
#   validation_method = "DNS"
# }

# Certificate validation records already exist - commented out to avoid conflicts
# resource "aws_route53_record" "ven_cert_validation" {
#   for_each = {
#     for dvo in aws_acm_certificate.ven.domain_validation_options :
#     dvo.domain_name => {
#       name  = dvo.resource_record_name
#       type  = dvo.resource_record_type
#       value = dvo.resource_record_value
#     }
#   }
#   zone_id = data.aws_route53_zone.gridcircuit.zone_id
#   name    = each.value.name
#   type    = each.value.type
#   records = [each.value.value]
#   ttl     = 60
# }

# Use existing certificate validation - imported certificate is already validated
data "aws_acm_certificate" "ven_validated" {
  domain   = "sim.gridcircuit.link"
  statuses = ["ISSUED"]
}
