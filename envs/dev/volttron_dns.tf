# DNS alias already exists - commented out to avoid conflicts
# resource "aws_route53_record" "ven_alias" {
#   zone_id = data.aws_route53_zone.gridcircuit.zone_id
#   name    = "sim.gridcircuit.link"
#   type    = "A"
#   alias {
#     name                   = module.volttron_alb.dns_name
#     zone_id                = module.volttron_alb.lb_zone_id
#     evaluate_target_health = false
#   }
# }

