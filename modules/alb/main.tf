variable "name" {}
variable "vpc_id" {}
variable "public_subnets" { type = list(string) }
variable "subnet_ids" {
  type        = list(string)
  description = "Subnets to place the load balancer in"
  default     = null
}
variable "internal" {
  type        = bool
  description = "Whether the ALB is internal"
  default     = false
}
variable "allowed_cidrs" {
  type        = list(string)
  description = "CIDR blocks allowed to access the listener"
  default     = ["0.0.0.0/0"]
}
variable "listener_port" { default = 80 }            # HTTP
variable "target_port" { default = 8000 }            # ←  changed
variable "health_check_path" { default = "/health" } # ←  changed
variable "acm_cert_arn" {
  type        = string
  description = "ARN of the ACM certificate for HTTPS"
  default     = null
}

variable "enable_https" {
  type        = bool
  description = "Enable HTTPS listener and 80->443 redirect"
  default     = false
}

locals {
  alb_ingress_ports = var.enable_https ? [var.listener_port, 443] : [var.listener_port]
}

# --- ALB security-group -----------------------------------------------------
resource "aws_security_group" "alb_sg" {
  name   = "${var.name}-sg"
  vpc_id = var.vpc_id

  egress {
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }

  lifecycle { prevent_destroy = true }
}

# HTTP :80 always (for redirect and/or plain HTTP)
resource "aws_security_group_rule" "alb_http_ingress" {
  type              = "ingress"
  protocol          = "tcp"
  from_port         = 80
  to_port           = 80
  cidr_blocks       = var.allowed_cidrs
  security_group_id = aws_security_group.alb_sg.id
}

# HTTPS :443 only when enabled
resource "aws_security_group_rule" "alb_https_ingress" {
  count             = var.enable_https ? 1 : 0
  type              = "ingress"
  protocol          = "tcp"
  from_port         = 443
  to_port           = 443
  cidr_blocks       = var.allowed_cidrs
  security_group_id = aws_security_group.alb_sg.id
}

# --- ALB --------------------------------------------------------------------
resource "aws_lb" "this" {
  name               = var.name
  load_balancer_type = "application"
  internal           = var.internal
  subnets            = var.subnet_ids != null ? var.subnet_ids : var.public_subnets
  security_groups    = [aws_security_group.alb_sg.id]

  lifecycle {
    prevent_destroy = true
  }
}

# --- Target group (port 8000) ----------------------------------------------
resource "aws_lb_target_group" "this" {
  name        = "${var.name}-tg"
  port        = var.target_port # 8000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    path                = var.health_check_path # /health
    protocol            = "HTTP"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }

  lifecycle {
    prevent_destroy = true
  }
}

# --- HTTP listener ----------------------------------------------------------
# Create an HTTP listener that either forwards to the target group or
# redirects to HTTPS when a certificate is provided.
resource "aws_lb_listener" "http" {
  count             = var.enable_https ? 0 : 1
  load_balancer_arn = aws_lb.this.arn
  port              = var.listener_port # 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this.arn
  }
}

resource "aws_lb_listener" "http_redirect" {
  count             = var.enable_https ? 1 : 0
  load_balancer_arn = aws_lb.this.arn
  port              = var.listener_port # 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      protocol    = "HTTPS"
      port        = "443"
      status_code = "HTTP_301"
    }
  }
}

# Optional HTTPS listener
resource "aws_lb_listener" "https" {
  count             = var.enable_https ? 1 : 0
  load_balancer_arn = aws_lb.this.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = var.acm_cert_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this.arn
  }
}


output "dns_name" { value = aws_lb.this.dns_name }
output "target_group_arn" { value = aws_lb_target_group.this.arn }
output "security_group_id" { value = aws_security_group.alb_sg.id }

# Expose the listener and target group resources so that other modules can
# explicitly depend on them. This prevents race conditions when creating
# resources like ECS services that reference these objects via variables.
output "listener" {
  value = var.enable_https ? aws_lb_listener.https[0] : aws_lb_listener.http[0]
}

output "target_group" {
  value = aws_lb_target_group.this
}

output "lb_zone_id" {
  value = aws_lb.this.zone_id
}

