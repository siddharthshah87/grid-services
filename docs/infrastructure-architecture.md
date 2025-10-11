# Infrastructure Architecture Documentation

This document provides a comprehensive overview of the AWS infrastructure architecture for the Grid Services platform.

## Architecture Overview

The Grid Services infrastructure is built on AWS using a microservices architecture with the following key components:

- **VPC** - Isolated network environment
- **ECS Fargate** - Containerized service orchestration  
- **IoT Core** - Device communication and management
- **RDS PostgreSQL** - Data persistence
- **Application Load Balancer** - Traffic routing and SSL termination
- **ECR** - Container image registry

## High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                              Internet                                │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
                    ┌─────▼─────┐
                    │    ALB    │ (Port 80/443)
                    │  (Public) │
                    └─────┬─────┘
                          │
┌─────────────────────────▼─────────────────────────────────────────────┐
│                        VPC (10.10.0.0/16)                            │
│  ┌─────────────────┐                    ┌─────────────────┐          │
│  │  Public Subnet  │                    │  Public Subnet  │          │
│  │   10.10.1.0/24  │                    │   10.10.2.0/24  │          │
│  │      AZ-a       │                    │      AZ-b       │          │
│  │                 │                    │                 │          │
│  │  ┌───────────┐  │                    │  ┌───────────┐  │          │
│  │  │    ECS    │  │                    │  │    ECS    │  │          │
│  │  │ Services  │  │                    │  │ Services  │  │          │
│  │  └───────────┘  │                    │  └───────────┘  │          │
│  └─────────────────┘                    └─────────────────┘          │
│                                                                       │
│  ┌─────────────────┐                    ┌─────────────────┐          │
│  │ Private Subnet  │                    │ Private Subnet  │          │
│  │   10.10.3.0/24  │                    │   10.10.4.0/24  │          │
│  │      AZ-a       │                    │      AZ-b       │          │
│  │                 │                    │                 │          │
│  │  ┌───────────┐  │                    │  ┌───────────┐  │          │
│  │  │    RDS    │  │                    │  │    RDS    │  │          │
│  │  │PostgreSQL │  │                    │  │ (Standby) │  │          │
│  │  └───────────┘  │                    │  └───────────┘  │          │
│  └─────────────────┘                    └─────────────────┘          │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                     IoT Core VPC Endpoint                      │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────┘
                          │
              ┌───────────▼───────────┐
              │      AWS IoT Core     │
              │  (Device Management)  │
              └───────────────────────┘
```

## Network Architecture

### VPC Configuration
- **CIDR Block**: `10.10.0.0/16`
- **Availability Zones**: 2 (for high availability)
- **Subnets**:
  - Public: `10.10.1.0/24`, `10.10.2.0/24`
  - Private: `10.10.3.0/24`, `10.10.4.0/24`

### Subnet Design
```hcl
# VPC Module Configuration
module "vpc" {
  source     = "../../modules/vpc"
  name       = "hems-demo-vpc"
  cidr_block = "10.10.0.0/16"
  az_count   = 2
}
```

**Public Subnets**:
- Host ALB and ECS tasks with public IPs
- Internet Gateway for outbound access
- NAT Gateway for private subnet access

**Private Subnets**:
- Host RDS database instances
- Isolated from direct internet access
- Access via NAT Gateway in public subnets

### Security Groups

#### ECS Tasks Security Group
```hcl
module "ecs_security_group" {
  source = "../../modules/security-group"
  name   = "ecs-tasks-sg"
  vpc_id = module.vpc.vpc_id
}
```

**Inbound Rules**:
- Port 8000: Backend API (from ALB)
- Port 8080: Grid-Event Gateway (from ALB)
- Port 8081: VEN endpoints (from ALB)
- Port 3000: Frontend (from ALB)

**Outbound Rules**:
- All traffic to internet (0.0.0.0/0)
- PostgreSQL to RDS security group
- HTTPS to IoT Core endpoint

#### RDS Security Group
**Inbound Rules**:
- Port 5432: PostgreSQL (from ECS security group only)

**Outbound Rules**:
- None (database doesn't initiate outbound connections)

## Compute Architecture

### ECS Cluster
```hcl
module "ecs_cluster" {
  source = "../../modules/ecs-cluster"
  name   = "hems-ecs-cluster"
}
```

**Configuration**:
- **Compute**: Fargate (serverless containers)
- **Scaling**: Auto-scaling based on CPU/memory
- **Logging**: CloudWatch Logs integration
- **Monitoring**: CloudWatch metrics and alarms

### ECS Services

#### Backend Service
```hcl
module "ecs_service_backend" {
  source = "../../modules/ecs-service-backend"
  # Service configuration
}
```

**Specifications**:
- **CPU**: 512 vCPU
- **Memory**: 1024 MB
- **Port**: 8000
- **Health Check**: `/health` endpoint
- **Desired Count**: 1 (scalable to 5)

#### Grid-Event Gateway Service
```hcl
module "ecs_service_grid_event_gateway" {
  source = "../../modules/ecs-service-openadr"
  # VTN server configuration
}
```

**Specifications**:
- **CPU**: 256 vCPU
- **Memory**: 512 MB
- **Ports**: 8080 (HTTP), 8081 (VEN API)
- **Health Check**: `/health` endpoint

#### Volttron VEN Service  
```hcl
module "ecs_service_volttron" {
  source = "../../modules/ecs-service-volttron"
  # VEN agent configuration
}
```

**Specifications**:
- **CPU**: 256 vCPU
- **Memory**: 512 MB
- **Port**: 8000
- **Health Check**: `/health` endpoint

#### Frontend Service
```hcl
module "ecs_service_frontend" {
  source = "../../modules/ecs-service-frontend"
  # React application
}
```

**Specifications**:
- **CPU**: 256 vCPU
- **Memory**: 512 MB
- **Port**: 3000
- **Health Check**: Root path `/`

## Data Architecture

### RDS PostgreSQL
```hcl
module "rds_postgresql" {
  source = "../../modules/rds-postgresql"
  # Database configuration
}
```

**Configuration**:
- **Engine**: PostgreSQL 15
- **Instance Class**: db.t3.micro (dev) / db.r5.large (prod)
- **Storage**: 20 GB (encrypted)
- **Multi-AZ**: Enabled for production
- **Backup Retention**: 7 days
- **Maintenance Window**: Sunday 03:00-04:00 UTC

**Database Schema**:
- `vens` - VEN device registry
- `loads` - Load/circuit definitions
- `events` - Demand response events
- `metrics` - Telemetry and performance data
- `network_stats` - Aggregated network statistics

### Container Registry (ECR)
```hcl
module "ecr_grid_event_gateway" {
  source = "../../modules/ecr-repo"
  name   = "grid-event-gateway"
}

module "ecr_volttron" {
  source = "../../modules/ecr-repo"
  name   = "volttron-ven"
}
```

**Repositories**:
- `grid-event-gateway` - OpenADR VTN server
- `volttron-ven` - VEN agent
- `ecs-backend` - FastAPI backend
- `ecs-frontend` - React frontend

**Image Lifecycle**:
- Lifecycle policies to retain latest 10 images
- Automatic cleanup of untagged images after 1 day

## IoT Architecture

### IoT Core Configuration
```hcl
module "iot_core" {
  source         = "../../modules/iot-core"
  prefix         = "volttron"
  enable_logging = true
}
```

**Components**:
- **Things**: VEN device registrations
- **Certificates**: X.509 certificates for MQTT TLS
- **Policies**: Permission policies for device operations
- **Device Shadows**: State synchronization between VEN and cloud

### MQTT Topics
```
ven/cmd/{venId}      # Commands to VEN (Backend → VEN)
ven/ack/{venId}      # Acknowledgments (VEN → Backend)
oadr/meter/{venId}   # Metering telemetry (VEN → Backend)
ven/loads/{venId}    # Load snapshots (VEN → Backend)
volttron/dev         # Development/debug messages
```

### IoT Rules and Data Flow
```hcl
module "iot_rule_forwarder" {
  source           = "../../modules/iot-rule-forwarder"
  rule_name_prefix = "mqtt-forward"
  topics           = ["openadr/event", "volttron/metering"]
}
```

**Data Pipeline**:
1. VEN publishes telemetry to IoT Core
2. IoT Rules forward messages to Kinesis
3. Backend consumes from MQTT topics
4. Data persisted to PostgreSQL
5. API serves aggregated data to frontend

### VPC Endpoint for IoT
```hcl
# Private IoT Core access
iot_data_endpoint = aws_vpc_endpoint.iot_data.dns_entry[0].dns_name
```

**Benefits**:
- Private network access to IoT Core
- Reduced data transfer costs
- Enhanced security (no internet routing)

## Load Balancing Architecture

### Application Load Balancer
```hcl
module "grid_event_gateway_alb" {
  source            = "../../modules/alb"
  name              = "grid-event-gateway-alb"
  vpc_id            = module.vpc.vpc_id
  public_subnets    = module.vpc.public_subnets
  listener_port     = 80
  target_port       = 8080
  health_check_path = "/health"
}
```

### Traffic Routing
```
Internet → ALB → Target Groups → ECS Tasks

ALB Listeners:
- Port 80/443 → Grid-Event Gateway (8080)
- Port 80/443 → Backend API (8000)  
- Port 80/443 → Frontend (3000)
- Port 80/443 → VEN Agent (8000)
```

### SSL/TLS Termination
```hcl
# ACM Certificate for ALB
resource "aws_acm_certificate" "frontend" {
  domain_name       = "gridcircuit.link"
  validation_method = "DNS"
}
```

**Certificate Management**:
- ACM certificates for public endpoints
- Automatic renewal for DNS-validated certificates
- SNI support for multiple domains

## Identity and Access Management

### IAM Roles Architecture

#### ECS Task Execution Role
```hcl
module "ecs_task_roles" {
  source         = "../../modules/iam-roles/ecs_task_roles"
  name_prefix    = "grid-sim"
  tls_secret_arn = aws_secretsmanager_secret.volttron_tls.arn
}
```

**Permissions**:
- ECR image pulling
- CloudWatch Logs writing
- Secrets Manager access
- ECS task execution

#### ECS Task Role (IoT MQTT)
**Permissions**:
- IoT Core device communication
- IoT Device Shadow access
- IoT message publishing/subscribing
- CloudWatch metrics publishing

#### ECS Task Role (Backend)
**Permissions**:
- RDS database access
- Secrets Manager access (DB credentials)
- CloudWatch Logs writing
- IoT Core message consumption

### Security Policies

#### IoT Device Policy
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "iot:Connect",
        "iot:Publish",
        "iot:Subscribe",
        "iot:Receive"
      ],
      "Resource": "arn:aws:iot:*:*:*"
    },
    {
      "Effect": "Allow", 
      "Action": [
        "iot:GetThingShadow",
        "iot:UpdateThingShadow"
      ],
      "Resource": "arn:aws:iot:*:*:thing/${iot:Connection.Thing.ThingName}"
    }
  ]
}
```

## Secrets Management

### AWS Secrets Manager
```hcl
resource "aws_secretsmanager_secret" "volttron_tls" {
  name        = "volttron-tls-cert"
  description = "TLS certificates for Volttron VEN"
}
```

**Stored Secrets**:
- `volttron-tls-cert` - IoT Core certificates (PEM format)
- `database-credentials` - RDS username/password
- `api-keys` - External service API keys

### Environment Variable Injection
```hcl
environment_secrets = [
  {
    name      = "CERT_BUNDLE_JSON"
    valueFrom = aws_secretsmanager_secret.volttron_tls.arn
  }
]
```

**Security Features**:
- Secrets encrypted at rest
- Automatic rotation support
- Fine-grained access control
- Audit logging via CloudTrail

## Monitoring and Logging

### CloudWatch Integration
```
ECS Services → CloudWatch Logs Groups:
- /ecs/grid-services-dev/backend
- /ecs/grid-services-dev/grid-event-gateway  
- /ecs/grid-services-dev/volttron-ven
- /ecs/grid-services-dev/frontend
```

### Metrics and Alarms
**Service Metrics**:
- CPU utilization
- Memory utilization
- Request count/latency
- Error rates

**Infrastructure Metrics**:
- ALB request count/latency
- RDS connections/performance
- IoT message volume
- ECS service health

### Log Aggregation
```hcl
module "iot_rule_forwarder" {
  # MQTT messages → S3 + Kinesis
  topics = ["openadr/event", "volttron/metering"]
}
```

**Log Destinations**:
- CloudWatch Logs (application logs)
- S3 (MQTT message archive)
- Kinesis (real-time processing)

## Scalability and Performance

### Auto Scaling Configuration
```hcl
resource "aws_appautoscaling_target" "backend" {
  service_namespace  = "ecs"
  resource_id        = "service/cluster/backend-service"
  scalable_dimension = "ecs:service:DesiredCount"
  min_capacity       = 1
  max_capacity       = 5
}
```

### Performance Optimizations
- **ECS**: Right-sized CPU/memory allocations
- **RDS**: Connection pooling and read replicas
- **ALB**: Health check optimizations
- **IoT**: Message batching and efficient topic design

## Disaster Recovery

### Backup Strategy
- **RDS**: Automated backups with 7-day retention
- **Secrets**: Cross-region replication available
- **Code**: Git repository with multiple remotes
- **Infrastructure**: Terraform state in S3 with versioning

### High Availability
- **Multi-AZ**: RDS and ECS services across availability zones
- **Load Balancing**: ALB distributes traffic across healthy targets
- **Health Checks**: Automatic replacement of unhealthy instances

## Cost Optimization

### Resource Right-Sizing
- **Fargate**: Pay-per-use computing
- **RDS**: Instance class optimization
- **Data Transfer**: VPC endpoints reduce NAT costs
- **Storage**: Lifecycle policies for logs and images

### Reserved Capacity
- RDS Reserved Instances for predictable workloads
- Savings Plans for consistent compute usage

## Security Architecture

### Network Security
- **VPC**: Isolated network environment
- **Security Groups**: Firewall rules at instance level
- **NACLs**: Subnet-level access control
- **Private Subnets**: Database isolation

### Data Security
- **Encryption at Rest**: RDS, S3, EBS volumes
- **Encryption in Transit**: TLS for all communications
- **Secrets Management**: AWS Secrets Manager integration
- **Certificate Management**: ACM for public endpoints

### Access Control
- **IAM**: Least privilege access policies
- **MFA**: Multi-factor authentication for administrative access
- **Audit**: CloudTrail logging for all API calls

## Future Architecture Considerations

### Potential Enhancements
1. **Container Orchestration**: Migration to EKS for advanced features
2. **Data Analytics**: Real-time stream processing with Kinesis Analytics  
3. **Machine Learning**: ML pipeline for demand forecasting
4. **Global Distribution**: CloudFront CDN for frontend assets
5. **Compliance**: AWS Config for compliance monitoring

### Scalability Roadmap
1. **Database Sharding**: Horizontal scaling for large deployments
2. **Microservices**: Further decomposition of backend services
3. **Event-Driven Architecture**: SQS/SNS for asynchronous processing
4. **Caching Layer**: ElastiCache for frequently accessed data

This architecture provides a robust, scalable, and secure foundation for the Grid Services platform while maintaining operational simplicity and cost-effectiveness.