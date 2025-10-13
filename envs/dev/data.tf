# Data sources for existing AWS infrastructure
data "aws_vpc" "existing" {
  id = "vpc-0aab765c09cbb8f2b"
}

data "aws_subnets" "public" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.existing.id]
  }

  filter {
    name   = "tag:Tier"
    values = ["public"]
  }
}

data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.existing.id]
  }

  filter {
    name   = "tag:Tier"
    values = ["private"]
  }
}

data "aws_security_group" "ecs_tasks" {
  name   = "ecs-tasks-sg"
  vpc_id = data.aws_vpc.existing.id
}

data "aws_security_group" "secrets_endpoint" {
  name   = "secrets-endpoint-sg"
  vpc_id = data.aws_vpc.existing.id
}

data "aws_internet_gateway" "existing" {
  filter {
    name   = "attachment.vpc-id"
    values = [data.aws_vpc.existing.id]
  }
}

# Get IoT data endpoint
data "aws_iot_endpoint" "data" {
  endpoint_type = "iot:Data-ATS"
}

# Get IoT Core VPC endpoint for private connectivity
data "aws_vpc_endpoint" "iot_data" {
  vpc_id       = data.aws_vpc.existing.id
  service_name = "com.amazonaws.us-west-2.iot.data"
}