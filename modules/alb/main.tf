variable "name" {}
variable "vpc_id" {}
variable "public_subnets" { type = list(string) }
variable "listener_port" { default = 80 }            # HTTP
variable "target_port" { default = 8000 }            # ←  changed
variable "health_check_path" { default = "/health" } # ←  changed

# --- ALB security-group -----------------------------------------------------
resource "aws_security_group" "alb_sg" {
  name   = "${var.name}-sg"
  vpc_id = var.vpc_id

  # Permit internet → ALB listener
  ingress {
    protocol    = "tcp"
    from_port   = var.listener_port
    to_port     = var.listener_port
    cidr_blocks = ["0.0.0.0/0"]
  }

  # ALB → targets (any port; SG on the tasks restricts to 8000)
  egress {
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# --- ALB --------------------------------------------------------------------
resource "aws_lb" "this" {
  name               = var.name
  load_balancer_type = "application"
  subnets            = var.public_subnets
  security_groups    = [aws_security_group.alb_sg.id]
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
}

# --- HTTP listener ----------------------------------------------------------
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.this.arn
  port              = var.listener_port # 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this.arn
  }
}

# (Optional) HTTPS listener example
# resource "aws_lb_listener" "https" {
#   load_balancer_arn = aws_lb.this.arn
#   port              = 443
#   protocol          = "HTTPS"
#   ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
#   certificate_arn   = var.acm_cert_arn
#
#   default_action {
#     type             = "forward"
#     target_group_arn = aws_lb_target_group.this.arn
#   }
# }

output "dns_name" { value = aws_lb.this.dns_name }
output "target_group_arn" { value = aws_lb_target_group.this.arn }

