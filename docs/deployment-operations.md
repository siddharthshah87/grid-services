# Deployment and Operations Guide

This guide covers deploying the Grid Services infrastructure to AWS and managing operational procedures.

## Overview

The Grid Services infrastructure deploys on AWS using:
- **Terraform** for infrastructure as code
- **ECS Fargate** for containerized services
- **ECR** for Docker image registry
- **IoT Core** for device communication
- **RDS PostgreSQL** for data persistence
- **Application Load Balancer** for traffic routing

## Pre-Deployment Setup

### AWS Account Prerequisites
- AWS account with sufficient permissions
- AWS CLI configured with appropriate credentials
- Terraform backend storage (S3 bucket + DynamoDB table)

### Bootstrap Terraform State
Create the required S3 bucket and DynamoDB table for Terraform state management:

```bash
# Run the bootstrap script
./scripts/bootstrap_state.sh

# Or manually specify region
AWS_REGION=us-east-1 ./scripts/bootstrap_state.sh
```

This creates:
- S3 bucket: `tf-state-<account-id>`
- DynamoDB table: `tf-lock-<account-id>`

### Verify Prerequisites
```bash
# Check AWS credentials
aws sts get-caller-identity

# Check Terraform installation
terraform version

# Check Docker installation
docker version
```

## Docker Image Management

### ECR Authentication
```bash
# Authenticate Docker to ECR
./scripts/ecr-login.sh

# Or with specific profile
AWS_PROFILE=your-profile ./scripts/ecr-login.sh
```

### Building and Pushing Images

#### Grid-Event Gateway (VTN)
```bash
cd grid-event-gateway
./build_and_push.sh

# Or manually
docker build -t grid-event-gateway:latest .
docker tag grid-event-gateway:latest \
  <account-id>.dkr.ecr.us-west-2.amazonaws.com/grid-event-gateway:latest
docker push <account-id>.dkr.ecr.us-west-2.amazonaws.com/grid-event-gateway:latest
```

#### Volttron VEN Agent
```bash
cd volttron-ven
./build_and_push.sh
```

#### ECS Backend
```bash
cd ecs-backend
./build_and_push.sh
```

#### ECS Frontend
```bash
cd ecs-frontend
./build_and_push.sh
```

### Image Versioning
Images are tagged with:
- `latest` - most recent build
- `<git-sha>` - specific commit
- `v<version>` - semantic versioning

## Infrastructure Deployment

### Development Environment
```bash
cd envs/dev

# Initialize Terraform workspace
./terraform_init.sh

# Or manually
terraform init
terraform plan
terraform apply
```

### Environment Configuration
Key variables in `envs/dev/variables.tf`:

```hcl
variable "aws_region" {
  default = "us-west-2"
}

variable "prefix" {
  default = "dev"
}

variable "enable_volttron_alb_rule" {
  default = true
}

variable "volttron_port" {
  default = 8000
}
```

### Terraform Deployment Process
```bash
cd envs/dev

# 1. Initialize
terraform init

# 2. Plan changes
terraform plan -out=tfplan

# 3. Apply changes
terraform apply tfplan

# 4. Verify deployment
terraform output
```

## Post-Deployment Configuration

### Capture IoT Certificates
```bash
cd envs/dev

# Extract certificates for MQTT TLS
terraform output -raw certificate_pem > client.crt
terraform output -raw private_key > client.key

# Set environment variables for services
export CLIENT_CERT=$(terraform output -raw certificate_pem)
export PRIVATE_KEY=$(terraform output -raw private_key)
export CA_CERT=$CLIENT_CERT
```

### Retrieve Infrastructure Outputs
```bash
# Get all outputs
terraform output

# Specific outputs
export THING_NAME=$(terraform output -raw thing_name)
export IOT_ENDPOINT=$(terraform output -raw iot_endpoint)
export VEN_URL=$(terraform output -raw volttron_url)
export BACKEND_URL=$(terraform output -raw backend_url)
```

### Verify Services
```bash
# Check ALB health
./scripts/ecs-alb-health.sh

# Check ECS service status
aws ecs describe-services \
  --cluster grid-services-dev \
  --services backend-service volttron-service grid-event-gateway-service

# Test endpoints
curl -f $BACKEND_URL/health
curl -f $VEN_URL/health
```

## Service Management

### ECS Service Operations

#### Viewing Service Status
```bash
# List all services
aws ecs list-services --cluster grid-services-dev

# Describe specific service
aws ecs describe-services \
  --cluster grid-services-dev \
  --services backend-service

# View service events
aws ecs describe-services \
  --cluster grid-services-dev \
  --services backend-service \
  --query 'services[0].events[:10]'
```

#### Scaling Services
```bash
# Scale backend service
aws ecs update-service \
  --cluster grid-services-dev \
  --service backend-service \
  --desired-count 2

# Auto-scaling based on CPU/memory
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/grid-services-dev/backend-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 1 \
  --max-capacity 5
```

#### Service Updates
```bash
# Force new deployment (latest image)
aws ecs update-service \
  --cluster grid-services-dev \
  --service backend-service \
  --force-new-deployment

# Update service with new task definition
aws ecs update-service \
  --cluster grid-services-dev \
  --service backend-service \
  --task-definition backend-task:2
```

### Service Redeployment
```bash
# Use provided redeployment script
./redeploy_service.sh backend-service

# Or for specific service
cd grid-event-gateway
./redeploy_service.sh
```

## Database Management

### RDS PostgreSQL Operations

#### Connection Information
```bash
# Get RDS endpoint from Terraform
DB_ENDPOINT=$(terraform output -raw db_endpoint)
DB_NAME=$(terraform output -raw db_name)

# Connect to database
psql -h $DB_ENDPOINT -U postgres -d $DB_NAME
```

#### Database Migrations
```bash
# Run migrations in ECS task
aws ecs run-task \
  --cluster grid-services-dev \
  --task-definition backend-task \
  --overrides '{
    "containerOverrides": [{
      "name": "backend",
      "command": ["alembic", "upgrade", "head"]
    }]
  }'
```

#### Backup and Restore
```bash
# Create RDS snapshot
aws rds create-db-snapshot \
  --db-instance-identifier grid-services-dev-db \
  --db-snapshot-identifier grid-services-dev-backup-$(date +%Y%m%d)

# List snapshots
aws rds describe-db-snapshots \
  --db-instance-identifier grid-services-dev-db
```

## IoT Core Management

### Thing and Certificate Management
```bash
# List IoT Things
aws iot list-things

# Get Thing details
aws iot describe-thing --thing-name $THING_NAME

# List certificates
aws iot list-certificates

# Update Thing attributes
aws iot update-thing \
  --thing-name $THING_NAME \
  --thing-type-name VEN \
  --attribute-payload '{"attributes":{"version":"1.0","location":"datacenter-1"}}'
```

### Device Shadow Operations
```bash
# Get Thing Shadow
aws iot-data get-thing-shadow \
  --thing-name $THING_NAME \
  shadow.json

# Update Thing Shadow
aws iot-data update-thing-shadow \
  --thing-name $THING_NAME \
  --cli-binary-format raw-in-base64-out \
  --payload '{"state":{"desired":{"report_interval_seconds":5}}}' \
  update-response.json
```

### MQTT Topic Monitoring
```bash
# List topic rules
aws iot list-topic-rules

# Get MQTT log bucket and stream
LOG_BUCKET=$(terraform output -raw log_bucket_name)
LOG_STREAM=$(terraform output -raw log_stream_name)

# Check S3 logs
aws s3 ls s3://$LOG_BUCKET/ --recursive

# Read Kinesis stream
aws kinesis get-records \
  --shard-iterator $(aws kinesis get-shard-iterator \
    --stream-name $LOG_STREAM \
    --shard-id shardId-000000000000 \
    --shard-iterator-type TRIM_HORIZON \
    --query ShardIterator --output text) \
  --limit 10
```

## Monitoring and Logging

### CloudWatch Logs
```bash
# List log groups
aws logs describe-log-groups --log-group-name-prefix "/ecs/grid-services"

# View recent logs
aws logs filter-log-events \
  --log-group-name "/ecs/grid-services-dev/backend" \
  --start-time $(date -d '1 hour ago' +%s)000

# Follow logs in real-time
aws logs tail "/ecs/grid-services-dev/backend" --follow
```

### ECS Task Monitoring
```bash
# List running tasks
aws ecs list-tasks --cluster grid-services-dev

# Describe task details
aws ecs describe-tasks \
  --cluster grid-services-dev \
  --tasks <task-arn>

# Get task metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=backend-service Name=ClusterName,Value=grid-services-dev \
  --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average
```

### Application Health Checks
```bash
# Backend health
curl -f https://api.gridcircuit.link/health

# VEN health
curl -f https://sim.gridcircuit.link/health

# ALB health check script
./scripts/ecs-alb-health.sh
```

## Secrets Management

### AWS Secrets Manager
```bash
# List secrets
aws secretsmanager list-secrets

# Get secret value
aws secretsmanager get-secret-value \
  --secret-id grid-services/dev/database \
  --query SecretString --output text

# Update secret
aws secretsmanager update-secret \
  --secret-id grid-services/dev/database \
  --secret-string '{"username":"postgres","password":"new-password"}'
```

### Environment Variable Management
```bash
# Update ECS service environment variables
aws ecs register-task-definition \
  --family backend-task \
  --container-definitions '[{
    "name": "backend",
    "environment": [
      {"name": "LOG_LEVEL", "value": "DEBUG"}
    ]
  }]'
```

## Certificate Rotation

### IoT Core Certificate Rotation
```bash
# Create new certificate
aws iot create-keys-and-certificate \
  --set-as-active \
  --certificate-pem-outfile new-cert.pem \
  --private-key-outfile new-private.key

# Update IoT policy attachment
NEW_CERT_ARN=$(aws iot list-certificates --query 'certificates[0].certificateArn' --output text)
aws iot attach-policy \
  --policy-name VENPolicy \
  --target $NEW_CERT_ARN

# Update Terraform with new certificate
# Edit envs/dev/main.tf and apply changes
```

### TLS Certificate Renewal (ACM)
```bash
# List ACM certificates
aws acm list-certificates

# Request certificate renewal (auto-renews if DNS validation)
aws acm resend-validation-email \
  --certificate-arn $CERT_ARN \
  --domain gridcircuit.link \
  --validation-domain gridcircuit.link
```

## Cleanup Operations

### Selective Cleanup
```bash
# Clean up ECS services only
./scripts/cleanup_ecs_services.sh

# Force cleanup stuck services
./scripts/ecs_force_cleanup.sh
```

### Full Environment Cleanup
```bash
cd envs/dev

# Destroy all resources
terraform destroy

# Or use cleanup script
./scripts/cleanup.sh
```

### Reset Environment
```bash
# Reset and redeploy
./scripts/reset_env.sh
```

## Troubleshooting

### Common Deployment Issues

#### Terraform State Issues
```bash
# Refresh state
terraform refresh

# Import existing resources
terraform import aws_ecs_service.backend service-name

# Force unlock state
terraform force-unlock <lock-id>
```

#### ECS Service Issues
```bash
# Check service events
aws ecs describe-services \
  --cluster grid-services-dev \
  --services backend-service \
  --query 'services[0].events[:5]'

# Check task definition
aws ecs describe-task-definition --task-definition backend-task

# View task logs
aws logs filter-log-events \
  --log-group-name "/ecs/grid-services-dev/backend" \
  --filter-pattern "ERROR"
```

#### Load Balancer Issues
```bash
# Check target health
aws elbv2 describe-target-health \
  --target-group-arn <target-group-arn>

# Check ALB logs (if enabled)
aws s3 ls s3://alb-logs-bucket/AWSLogs/<account-id>/elasticloadbalancing/
```

### Performance Optimization

#### ECS Resource Allocation
```hcl
# Adjust task definition resources
resource "aws_ecs_task_definition" "backend" {
  cpu    = "1024"  # Increase CPU
  memory = "2048"  # Increase memory
}
```

#### Auto Scaling Configuration
```hcl
# Enable auto scaling
resource "aws_appautoscaling_target" "backend" {
  service_namespace  = "ecs"
  resource_id        = "service/grid-services-dev/backend-service"
  scalable_dimension = "ecs:service:DesiredCount"
  min_capacity       = 1
  max_capacity       = 5
}
```

## Security Best Practices

### IAM Policies
- Use least privilege access
- Regular policy audits
- Separate roles for different services

### Network Security
- VPC with private subnets for databases
- Security groups with minimal required ports
- NAT Gateway for outbound internet access

### Data Protection
- Encryption at rest for RDS
- Encryption in transit for all connections
- Secrets stored in AWS Secrets Manager

## Automation and CI/CD

### GitHub Actions Integration
The repository includes workflows for:
- `terraform-plan.yml` - Plan Terraform changes
- `terraform-infra.yml` - Apply infrastructure changes
- `deploy-services.yml` - Deploy service updates
- `lint_and_test.yml` - Code quality checks

### Manual Deployment Scripts
```bash
# Deploy all services
./scripts/fix_and_apply.sh

# Check Terraform formatting
./scripts/check_terraform.sh
```

## Next Steps

After successful deployment:

1. Configure monitoring alerts in CloudWatch
2. Set up backup schedules for RDS
3. Implement log aggregation and analysis
4. Configure auto-scaling policies
5. Set up certificate renewal automation

## Support

For deployment issues:
1. Check CloudWatch logs for service errors
2. Verify security group and IAM permissions
3. Ensure all required environment variables are set
4. Check ALB target health status
5. Review Terraform state for drift