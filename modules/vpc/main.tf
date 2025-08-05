locals {
  interface_services = [
    "secretsmanager",
    "ecr.api",
    "ecr.dkr",
    "logs",
    "iot",
    "iot-data",
  ]
}

resource "aws_vpc" "this" {
  cidr_block           = var.cidr_block
  enable_dns_hostnames = true
  tags = merge(var.tags, {
    Name = "${var.name}"
  })
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.this.id
  tags   = var.tags
}

resource "aws_subnet" "public" {
  count                   = var.az_count
  vpc_id                  = aws_vpc.this.id
  cidr_block              = cidrsubnet(var.cidr_block, 4, count.index)
  availability_zone       = element(data.aws_availability_zones.azs.names, count.index)
  map_public_ip_on_launch = true
  tags = merge(var.tags, {
    Tier = "public"
  })
}

resource "aws_subnet" "private" {
  count                   = var.az_count
  vpc_id                  = aws_vpc.this.id
  cidr_block              = cidrsubnet(var.cidr_block, 4, count.index + 10)
  availability_zone       = element(data.aws_availability_zones.azs.names, count.index)
  map_public_ip_on_launch = false
  tags = merge(var.tags, {
    Tier = "private"
  })
}

resource "aws_security_group" "vpc_endpoints" {
  name        = "secrets-endpoint-sg"
  description = "Allow ECS tasks to hit Secrets Manager"
  vpc_id      = aws_vpc.this.id           # ← valid here

  ingress  {
    protocol                 = "tcp"
    from_port                = 443
    to_port                  = 443
    security_groups          = [var.ecs_tasks_sg_id]  # see note below
    description              = "ECS tasks to interface endpoints"
  }

  egress  {
    protocol  = "-1"
    from_port = 0
    to_port   = 0
    cidr_blocks = ["0.0.0.0/0"]
  }
}


resource "aws_vpc_endpoint" "interface" {
  for_each = toset(local.interface_services)

  vpc_id            = aws_vpc.this.id
  service_name      = "com.amazonaws.${data.aws_region.current.name}.${each.value}"
  vpc_endpoint_type = "Interface"

  subnet_ids         = aws_subnet.private[*].id
  security_group_ids = [aws_security_group.vpc_endpoints.id]

  private_dns_enabled = true
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.this.id
}

resource "aws_route_table_association" "private" {
  count          = length(aws_subnet.private)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

resource "aws_vpc_endpoint" "s3_gateway" {
  vpc_id            = aws_vpc.this.id
  service_name      = "com.amazonaws.${data.aws_region.current.name}.s3"
  vpc_endpoint_type = "Gateway"

  route_table_ids = [aws_route_table.private.id]
}

data "aws_availability_zones" "azs" {}
data "aws_region" "current" {}

