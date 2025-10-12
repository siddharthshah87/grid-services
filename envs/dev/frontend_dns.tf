# Look up the ALB to get its DNS name and zone ID (by name)
data "aws_lb" "frontend" {
  name = "frontend-alb"
}

# DNS alias already exists - commented out to avoid conflicts
# resource "aws_route53_record" "frontend_alias" {
#   zone_id = data.aws_route53_zone.gridcircuit.zone_id
#   name    = "app.gridcircuit.link"
#   type    = "A"
#   alias {
#     name                   = data.aws_lb.frontend.dns_name
#     zone_id                = data.aws_lb.frontend.zone_id
#     evaluate_target_health = false
#   }
# }

