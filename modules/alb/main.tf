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

# --- ALB security-group -----------------------------------------------------
resource "aws_security_group" "alb_sg" {
  name   = "${var.name}-sg"
  vpc_id = var.vpc_id

  # Permit traffic from allowed CIDRs to the listener
  ingress {
    protocol    = "tcp"
    from_port   = var.listener_port
    to_port     = var.listener_port
    cidr_blocks = var.allowed_cidrs
  }

  # Permit HTTPS traffic when a certificate is provided
  dynamic "ingress" {
    for_each = var.acm_cert_arn != null ? [1] : []
    content {
      protocol    = "tcp"
      from_port   = 443
      to_port     = 443
      cidr_blocks = var.allowed_cidrs
    }
  }

  # ALB → targets (any port; SG on the tasks restricts to 8000)
  egress {
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }

  lifecycle {
    prevent_destroy = true
  }
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
  count             = var.acm_cert_arn == null ? 1 : 0
  load_balancer_arn = aws_lb.this.arn
  port              = var.listener_port # 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this.arn
  }
}

resource "aws_lb_listener" "http_redirect" {
  count             = var.acm_cert_arn != null ? 1 : 0
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
  count             = var.acm_cert_arn != null ? 1 : 0
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
  # Export whichever listener forwards traffic to the target group. When a
  # certificate ARN is supplied, the HTTPS listener handles the forwarding and
  # the HTTP listener only performs redirects. Otherwise, the HTTP listener
  # forwards requests directly.
  value = var.acm_cert_arn == null ? aws_lb_listener.http[0] : aws_lb_listener.https[0]
}

output "target_group" {
  value = aws_lb_target_group.this
}

