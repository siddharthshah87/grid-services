# modules/security-group/main.tf

variable "name" {}
variable "vpc_id" {}
variable "allow_http" { default = true }
variable "alb_backend_sg_id" {
  type        = string
  description = "SG ID of the backend ALB"
  default     = null # allow the module to be used without a backend ALB
}

variable "alb_vtn_sg_id" {
  type        = string
  description = "SG ID of the VTN ALB"
  default     = null
}

variable "alb_volttron_sg_id" {
  type        = string
  description = "SG ID of the Volttron ALB"
  default     = null
}

variable "enable_alb_volttron_rule" {
  type        = bool
  description = "Whether to create the Volttron ALB ingress rule"
  default     = false
}

variable "volttron_port" {
  type        = number
  description = "Port used by the Volttron VEN health check"
  default     = 22916
}

resource "aws_security_group" "this" {
  name        = var.name
  description = "Security group for ECS tasks"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    self        = true
    description = "PostgreSQL access from ECS tasks and Aurora"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  dynamic "ingress" {
    for_each = var.allow_http ? [1] : []
    content {
      from_port   = 8080
      to_port     = 8080
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }

  tags = {
    Name = var.name
  }
}
resource "aws_security_group_rule" "from_alb_backend" {
  count                    = var.alb_backend_sg_id == null ? 0 : 1
  type                     = "ingress"
  from_port                = 8000
  to_port                  = 8000
  protocol                 = "tcp"
  security_group_id        = aws_security_group.this.id
  source_security_group_id = var.alb_backend_sg_id
}

resource "aws_security_group_rule" "from_alb_vtn" {
  count                    = var.alb_vtn_sg_id == null ? 0 : 1
  type                     = "ingress"
  from_port                = 8080
  to_port                  = 8080
  protocol                 = "tcp"
  security_group_id        = aws_security_group.this.id
  source_security_group_id = var.alb_vtn_sg_id
}

resource "aws_security_group_rule" "from_alb_volttron" {
  count                    = var.enable_alb_volttron_rule ? 1 : 0
  type                     = "ingress"
  from_port                = var.volttron_port
  to_port                  = var.volttron_port
  protocol                 = "tcp"
  security_group_id        = aws_security_group.this.id
  source_security_group_id = var.alb_volttron_sg_id
}

output "id" {
  value = aws_security_group.this.id
}

