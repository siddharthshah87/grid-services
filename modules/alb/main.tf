# modules/alb/main.tf
variable "name" {}
variable "vpc_id" {}
variable "public_subnets" { type = list(string) }
variable "listener_port" { default = 80 }
variable "target_port" { default = 8080 }
variable "health_check_path" { default = "/" }

resource "aws_security_group" "alb_sg" {
  name        = "${var.name}-sg"
  description = "Security group for ${var.name}"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = var.listener_port
    to_port     = var.listener_port
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.name}-sg"
  }
}

resource "aws_lb" "this" {
  name               = var.name
  load_balancer_type = "application"
  subnets            = var.public_subnets
  security_groups    = [aws_security_group.alb_sg.id]

  depends_on = [aws_security_group.alb_sg]

  tags = {
    Name = var.name
  }
}

resource "aws_lb_target_group" "this" {
  name        = "${var.name}-tg"
  port        = var.target_port
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    path                = var.health_check_path
    protocol            = "HTTP"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }
}

resource "aws_lb_listener" "this" {
  load_balancer_arn = aws_lb.this.arn
  port              = var.listener_port
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this.arn
  }

  depends_on = [aws_lb.this]
}

output "dns_name" {
  value = aws_lb.this.dns_name
}

output "target_group_arn" {
  value = aws_lb_target_group.this.arn
}

