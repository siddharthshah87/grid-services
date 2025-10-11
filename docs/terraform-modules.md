# Terraform Modules Reference

This document provides comprehensive reference documentation for all Terraform modules in the Grid Services infrastructure.

## Module Overview

The Grid Services infrastructure uses modular Terraform components to create reusable, maintainable infrastructure code. Each module encapsulates specific AWS resources and their configurations.

### Module Directory Structure
```
modules/
├── README.md                    # Module overview
├── alb/                        # Application Load Balancer
├── ecr-repo/                   # Elastic Container Registry
├ecs-cluster/                  # ECS Cluster
├── ecs-service-backend/        # Backend ECS Service
├── ecs-service-frontend/       # Frontend ECS Service  
├── ecs-service-openadr/        # OpenADR VTN Service
├── ecs-service-volttron/       # Volttron VEN Service
├── iam-roles/                  # IAM Roles and Policies
├── iot-core/                   # IoT Core Resources
├── iot-rule-forwarder/         # IoT Rule Engine
├── rds-postgresql/             # PostgreSQL Database
├── security-group/             # Security Groups
└── vpc/                        # Virtual Private Cloud
```

## Core Infrastructure Modules

### VPC Module (`modules/vpc/`)

Creates a Virtual Private Cloud with public and private subnets across multiple availability zones.

#### Input Variables
```hcl
variable "name" {
  type        = string
  description = "Name prefix for VPC resources"
}

variable "cidr_block" {
  type        = string
  description = "CIDR block for the VPC"
  default     = "10.0.0.0/16"
}

variable "az_count" {
  type        = number
  description = "Number of availability zones to use"
  default     = 2
}

variable "ecs_tasks_sg_id" {
  type        = string
  description = "Security group ID for ECS tasks"
}

variable "tags" {
  type        = map(string)
  description = "Tags to apply to all resources"
  default     = {}
}
```

#### Outputs
```hcl
output "vpc_id" {
  value = aws_vpc.this.id
}

output "public_subnets" {
  value = aws_subnet.public[*].id
}

output "private_subnets" {
  value = aws_subnet.private[*].id
}

output "internet_gateway_id" {
  value = aws_internet_gateway.igw.id
}

output "iot_data_endpoint_dns" {
  value = aws_vpc_endpoint.iot_data.dns_entry[0].dns_name
}
```

#### Usage Example
```hcl
module "vpc" {
  source     = "../../modules/vpc"
  name       = "grid-services-vpc"
  cidr_block = "10.10.0.0/16"
  az_count   = 2
  ecs_tasks_sg_id = module.ecs_security_group.id
  
  tags = {
    Project = "grid-services"
    Environment = "dev"
  }
}
```

#### Key Features
- **Multi-AZ Support**: Creates subnets across specified availability zones
- **Public/Private Subnets**: Separates public-facing and internal resources
- **VPC Endpoints**: Provides private access to AWS services
- **NAT Gateway**: Enables outbound internet access for private subnets
- **Internet Gateway**: Routes traffic between VPC and internet

### Application Load Balancer Module (`modules/alb/`)

Creates an Application Load Balancer with target groups and listeners for HTTP/HTTPS traffic.

#### Input Variables
```hcl
variable "name" {
  type        = string
  description = "Name for the ALB"
}

variable "vpc_id" {
  type        = string
  description = "VPC ID where ALB will be created"
}

variable "public_subnets" {
  type        = list(string)
  description = "Public subnet IDs for ALB placement"
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

variable "listener_port" {
  type        = number
  description = "Port for the listener"
  default     = 80
}

variable "target_port" {
  type        = number
  description = "Port where targets receive traffic"
  default     = 8000
}

variable "health_check_path" {
  type        = string
  description = "Path for health checks"
  default     = "/health"
}

variable "enable_https" {
  type        = bool
  description = "Enable HTTPS listener and HTTP->HTTPS redirect"
  default     = false
}

variable "acm_cert_arn" {
  type        = string
  description = "ARN of ACM certificate for HTTPS"
  default     = null
}
```

#### Outputs
```hcl
output "alb_arn" {
  value = aws_lb.this.arn
}

output "alb_dns_name" {
  value = aws_lb.this.dns_name
}

output "target_group_arn" {
  value = aws_lb_target_group.this.arn
}

output "listener" {
  value = aws_lb_listener.http
}

output "security_group_id" {
  value = aws_security_group.alb_sg.id
}
```

#### Usage Example
```hcl
module "backend_alb" {
  source            = "../../modules/alb"
  name              = "backend-alb"
  vpc_id            = module.vpc.vpc_id
  public_subnets    = module.vpc.public_subnets
  listener_port     = 80
  target_port       = 8000
  health_check_path = "/health"
  enable_https      = true
  acm_cert_arn      = aws_acm_certificate_validation.main.certificate_arn
}
```

### Security Group Module (`modules/security-group/`)

Creates security groups with configurable ingress and egress rules.

#### Input Variables
```hcl
variable "name" {
  type        = string
  description = "Name for the security group"
}

variable "vpc_id" {
  type        = string
  description = "VPC ID where security group will be created"
}

variable "description" {
  type        = string
  description = "Description for the security group"
  default     = ""
}

variable "tags" {
  type        = map(string)
  description = "Tags to apply to security group"
  default     = {}
}
```

#### Outputs
```hcl
output "id" {
  value = aws_security_group.this.id
}

output "arn" {
  value = aws_security_group.this.arn
}
```

## Container Infrastructure Modules

### ECS Cluster Module (`modules/ecs-cluster/`)

Creates an ECS cluster with Fargate capacity providers and optional CloudWatch insights.

#### Input Variables
```hcl
variable "name" {
  type        = string
  description = "Name for the ECS cluster"
}

variable "capacity_providers" {
  type        = list(string)
  description = "Capacity providers for the cluster"
  default     = ["FARGATE", "FARGATE_SPOT"]
}

variable "enable_insights" {
  type        = bool
  description = "Enable CloudWatch Container Insights"
  default     = true
}

variable "tags" {
  type        = map(string)
  description = "Tags to apply to cluster"
  default     = {}
}
```

#### Outputs
```hcl
output "id" {
  value = aws_ecs_cluster.this.id
}

output "name" {
  value = aws_ecs_cluster.this.name
}

output "arn" {
  value = aws_ecs_cluster.this.arn
}
```

#### Usage Example
```hcl
module "ecs_cluster" {
  source = "../../modules/ecs-cluster"
  name   = "grid-services-cluster"
  
  tags = {
    Project = "grid-services"
    Environment = "dev"
  }
}
```

### ECR Repository Module (`modules/ecr-repo/`)

Creates Elastic Container Registry repositories with lifecycle policies.

#### Input Variables
```hcl
variable "name" {
  type        = string
  description = "Name for the ECR repository"
}

variable "image_tag_mutability" {
  type        = string
  description = "Image tag mutability setting"
  default     = "MUTABLE"
}

variable "scan_on_push" {
  type        = bool
  description = "Enable image scanning on push"
  default     = true
}

variable "tags" {
  type        = map(string)
  description = "Tags to apply to repository"
  default     = {}
}
```

#### Outputs
```hcl
output "repository_url" {
  value = aws_ecr_repository.this.repository_url
}

output "repository_arn" {
  value = aws_ecr_repository.this.arn
}

output "registry_id" {
  value = aws_ecr_repository.this.registry_id
}
```

#### Usage Example
```hcl
module "ecr_backend" {
  source = "../../modules/ecr-repo"
  name   = "grid-services-backend"
  
  tags = {
    Project = "grid-services"
    Component = "backend"
  }
}
```

## ECS Service Modules

### Backend ECS Service (`modules/ecs-service-backend/`)

Creates an ECS service for the FastAPI backend with database connectivity.

#### Input Variables
```hcl
variable "name" {
  type        = string
  description = "Name for the ECS service"
}

variable "cluster_id" {
  type        = string
  description = "ECS cluster ID"
}

variable "image" {
  type        = string
  description = "Docker image URI"
}

variable "cpu" {
  type        = number
  description = "CPU units for the task"
  default     = 512
}

variable "memory" {
  type        = number
  description = "Memory in MB for the task"
  default     = 1024
}

variable "desired_count" {
  type        = number
  description = "Desired number of running tasks"
  default     = 1
}

variable "container_port" {
  type        = number
  description = "Port the container listens on"
  default     = 8000
}

variable "subnet_ids" {
  type        = list(string)
  description = "Subnet IDs for the service"
}

variable "security_group_id" {
  type        = string
  description = "Security group ID for the service"
}

variable "target_group_arn" {
  type        = string
  description = "ALB target group ARN"
}

variable "execution_role_arn" {
  type        = string
  description = "ECS task execution role ARN"
}

variable "task_role_arn" {
  type        = string
  description = "ECS task role ARN"
}

variable "environment_variables" {
  type        = list(object({
    name  = string
    value = string
  }))
  description = "Environment variables for the container"
  default     = []
}

variable "environment_secrets" {
  type        = list(object({
    name      = string
    valueFrom = string
  }))
  description = "Secrets from AWS Secrets Manager"
  default     = []
}
```

#### Outputs
```hcl
output "service_id" {
  value = aws_ecs_service.this.id
}

output "service_name" {
  value = aws_ecs_service.this.name
}

output "task_definition_arn" {
  value = aws_ecs_task_definition.this.arn
}
```

### VEN Agent ECS Service (`modules/ecs-service-volttron/`)

Creates an ECS service for the Volttron VEN agent with IoT Core integration.

#### Input Variables
Similar to backend service with additional IoT-specific variables:

```hcl
variable "iot_endpoint" {
  type        = string
  description = "IoT Core endpoint"
}

variable "iot_thing_name" {
  type        = string
  description = "IoT Thing name"
}

variable "mqtt_topics" {
  type        = object({
    metering   = string
    events     = string
    responses  = string
    status     = string
  })
  description = "MQTT topic configuration"
}
```

### OpenADR VTN Service (`modules/ecs-service-openadr/`)

Creates an ECS service for the Grid-Event Gateway (OpenADR VTN server).

#### Key Variables
```hcl
variable "mqtt_topic_events" {
  type        = string
  description = "MQTT topic for publishing events"
}

variable "mqtt_topic_responses" {
  type        = string
  description = "MQTT topic for receiving responses"
}

variable "mqtt_topic_metering" {
  type        = string
  description = "MQTT topic for metering data"
}

variable "vens_port" {
  type        = number
  description = "Port for VEN API endpoints"
  default     = 8081
}
```

## Data Infrastructure Modules

### RDS PostgreSQL Module (`modules/rds-postgresql/`)

Creates a PostgreSQL RDS instance with appropriate configuration for the application.

#### Input Variables
```hcl
variable "identifier" {
  type        = string
  description = "RDS instance identifier"
}

variable "instance_class" {
  type        = string
  description = "RDS instance class"
  default     = "db.t3.micro"
}

variable "allocated_storage" {
  type        = number
  description = "Allocated storage in GB"
  default     = 20
}

variable "storage_encrypted" {
  type        = bool
  description = "Enable storage encryption"
  default     = true
}

variable "engine_version" {
  type        = string
  description = "PostgreSQL engine version"
  default     = "15.3"
}

variable "database_name" {
  type        = string
  description = "Name of the database"
}

variable "username" {
  type        = string
  description = "Master username"
  default     = "postgres"
}

variable "password" {
  type        = string
  description = "Master password"
  sensitive   = true
}

variable "vpc_id" {
  type        = string
  description = "VPC ID for the database"
}

variable "subnet_ids" {
  type        = list(string)
  description = "Subnet IDs for database subnet group"
}

variable "security_group_ids" {
  type        = list(string)
  description = "Security group IDs for the database"
}

variable "backup_retention_period" {
  type        = number
  description = "Backup retention period in days"
  default     = 7
}

variable "multi_az" {
  type        = bool
  description = "Enable Multi-AZ deployment"
  default     = false
}

variable "tags" {
  type        = map(string)
  description = "Tags to apply to RDS resources"
  default     = {}
}
```

#### Outputs
```hcl
output "endpoint" {
  value = aws_db_instance.this.endpoint
}

output "port" {
  value = aws_db_instance.this.port
}

output "database_name" {
  value = aws_db_instance.this.db_name
}

output "username" {
  value = aws_db_instance.this.username
}

output "instance_id" {
  value = aws_db_instance.this.id
}
```

## IoT Infrastructure Modules

### IoT Core Module (`modules/iot-core/`)

Creates IoT Core resources including Things, certificates, and policies.

#### Input Variables
```hcl
variable "prefix" {
  type        = string
  description = "Prefix for IoT resource names"
}

variable "thing_type_name" {
  type        = string
  description = "IoT Thing Type name"
  default     = "VEN"
}

variable "enable_logging" {
  type        = bool
  description = "Enable IoT Core logging"
  default     = true
}

variable "log_level" {
  type        = string
  description = "IoT Core log level"
  default     = "INFO"
}

variable "tags" {
  type        = map(string)
  description = "Tags to apply to IoT resources"
  default     = {}
}
```

#### Outputs
```hcl
output "endpoint" {
  value = data.aws_iot_endpoint.endpoint.endpoint_address
}

output "thing_name" {
  value = aws_iot_thing.this.name
}

output "thing_arn" {
  value = aws_iot_thing.this.arn
}

output "certificate_arn" {
  value = aws_iot_certificate.this.arn
}

output "certificate_pem" {
  value = aws_iot_certificate.this.certificate_pem
  sensitive = true
}

output "private_key" {
  value = aws_iot_certificate.this.private_key
  sensitive = true
}

output "policy_name" {
  value = aws_iot_policy.this.name
}
```

### IoT Rule Forwarder Module (`modules/iot-rule-forwarder/`)

Creates IoT Rules to forward MQTT messages to S3 and Kinesis for processing and storage.

#### Input Variables
```hcl
variable "rule_name_prefix" {
  type        = string
  description = "Prefix for IoT rule names"
}

variable "topics" {
  type        = list(string)
  description = "MQTT topics to forward"
}

variable "s3_bucket_name" {
  type        = string
  description = "S3 bucket for message storage"
  default     = null
}

variable "kinesis_stream_name" {
  type        = string
  description = "Kinesis stream for real-time processing"
  default     = null
}

variable "create_s3_bucket" {
  type        = bool
  description = "Create S3 bucket for message storage"
  default     = true
}

variable "create_kinesis_stream" {
  type        = bool
  description = "Create Kinesis stream"
  default     = true
}
```

#### Outputs
```hcl
output "rule_names" {
  value = aws_iot_topic_rule.forwarder[*].name
}

output "s3_bucket_name" {
  value = var.create_s3_bucket ? aws_s3_bucket.mqtt_logs[0].id : var.s3_bucket_name
}

output "kinesis_stream_name" {
  value = var.create_kinesis_stream ? aws_kinesis_stream.mqtt_stream[0].name : var.kinesis_stream_name
}
```

## IAM Modules

### ECS Task Roles Module (`modules/iam-roles/ecs_task_roles/`)

Creates IAM roles and policies for ECS tasks with appropriate permissions.

#### Input Variables
```hcl
variable "name_prefix" {
  type        = string
  description = "Prefix for IAM role names"
}

variable "tls_secret_arn" {
  type        = string
  description = "ARN of Secrets Manager secret for TLS certificates"
}

variable "database_secret_arn" {
  type        = string
  description = "ARN of Secrets Manager secret for database credentials"
  default     = ""
}

variable "additional_policies" {
  type        = list(string)
  description = "Additional policy ARNs to attach"
  default     = []
}
```

#### Outputs
```hcl
output "execution" {
  value       = aws_iam_role.execution.arn
  description = "ECS task execution role ARN"
}

output "iot_mqtt" {
  value       = aws_iam_role.iot_mqtt.arn
  description = "IoT MQTT task role ARN"
}

output "backend" {
  value       = aws_iam_role.backend.arn
  description = "Backend task role ARN"
}
```

## Module Usage Patterns

### Complete Environment Example

```hcl
# envs/dev/main.tf

# VPC and Networking
module "vpc" {
  source            = "../../modules/vpc"
  name              = "grid-services-vpc"
  cidr_block        = "10.10.0.0/16"
  az_count          = 2
  ecs_tasks_sg_id   = module.ecs_security_group.id
}

# Security Groups
module "ecs_security_group" {
  source = "../../modules/security-group"
  name   = "ecs-tasks-sg"
  vpc_id = module.vpc.vpc_id
}

# ECS Cluster
module "ecs_cluster" {
  source = "../../modules/ecs-cluster"
  name   = "grid-services-cluster"
}

# IAM Roles
module "ecs_task_roles" {
  source            = "../../modules/iam-roles/ecs_task_roles"
  name_prefix       = "grid-services"
  tls_secret_arn    = aws_secretsmanager_secret.tls.arn
}

# Container Registry
module "ecr_backend" {
  source = "../../modules/ecr-repo"
  name   = "grid-services-backend"
}

# Database
module "database" {
  source               = "../../modules/rds-postgresql"
  identifier           = "grid-services-db"
  instance_class       = "db.t3.micro"
  database_name        = "grid_services"
  username             = "postgres"
  password             = var.db_password
  vpc_id               = module.vpc.vpc_id
  subnet_ids           = module.vpc.private_subnets
  security_group_ids   = [module.db_security_group.id]
}

# Load Balancer
module "alb" {
  source            = "../../modules/alb"
  name              = "grid-services-alb"
  vpc_id            = module.vpc.vpc_id
  public_subnets    = module.vpc.public_subnets
  enable_https      = true
  acm_cert_arn      = aws_acm_certificate_validation.main.certificate_arn
}

# Backend Service
module "backend_service" {
  source             = "../../modules/ecs-service-backend"
  name               = "backend"
  cluster_id         = module.ecs_cluster.id
  image              = "${module.ecr_backend.repository_url}:latest"
  subnet_ids         = module.vpc.public_subnets
  security_group_id  = module.ecs_security_group.id
  target_group_arn   = module.alb.target_group_arn
  execution_role_arn = module.ecs_task_roles.execution
  task_role_arn      = module.ecs_task_roles.backend

  environment_variables = [
    {
      name  = "DATABASE_URL"
      value = "postgresql://${module.database.username}:${var.db_password}@${module.database.endpoint}/${module.database.database_name}"
    }
  ]
}

# IoT Core
module "iot_core" {
  source = "../../modules/iot-core"
  prefix = "grid-services"
}

# VEN Service
module "ven_service" {
  source             = "../../modules/ecs-service-volttron"
  name               = "ven"
  cluster_id         = module.ecs_cluster.id
  image              = "${module.ecr_ven.repository_url}:latest"
  subnet_ids         = module.vpc.public_subnets
  security_group_id  = module.ecs_security_group.id
  execution_role_arn = module.ecs_task_roles.execution
  task_role_arn      = module.ecs_task_roles.iot_mqtt
  
  iot_endpoint       = module.iot_core.endpoint
  iot_thing_name     = module.iot_core.thing_name
}
```

## Module Development Guidelines

### Creating New Modules

1. **Directory Structure**:
   ```
   modules/new-module/
   ├── main.tf          # Primary resource definitions
   ├── variables.tf     # Input variables
   ├── outputs.tf       # Output values
   ├── data.tf          # Data sources (optional)
   └── README.md        # Module documentation
   ```

2. **Variable Naming Conventions**:
   - Use descriptive names: `database_name` instead of `db_name`
   - Group related variables: `mqtt_topic_*` for MQTT configurations
   - Use consistent types: `list(string)` for string arrays

3. **Output Conventions**:
   - Always output resource IDs and ARNs
   - Include useful attributes like DNS names, endpoints
   - Mark sensitive outputs appropriately

4. **Tagging Strategy**:
   - Accept `tags` variable for resource tagging
   - Merge provided tags with default module tags
   - Include consistent tags: Project, Environment, Component

### Module Testing

```bash
# Validate module syntax
terraform validate modules/new-module/

# Plan with example configuration
terraform plan -target=module.new_module

# Check for security issues
checkov -d modules/new-module/
```

### Module Versioning

For production use, consider:
- Git tags for module versions
- Semantic versioning (v1.0.0, v1.1.0, etc.)
- Terraform Registry publishing
- Change documentation and migration guides

This reference provides comprehensive documentation for understanding, using, and maintaining the Terraform modules in the Grid Services infrastructure.