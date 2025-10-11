# Scripts Reference Guide

This document provides comprehensive reference for all utility scripts in the Grid Services repository.

## Scripts Overview

The `scripts/` directory contains automation tools, testing utilities, and operational scripts for managing the Grid Services infrastructure.

### Script Categories

```
scripts/
├── Infrastructure & Setup
│   ├── authenticate_aws.sh          # AWS SSO authentication
│   ├── bootstrap_state.sh           # Terraform state setup
│   ├── install_awscli.sh           # AWS CLI installation
│   ├── install_docker.sh           # Docker installation
│   └── install_terraform.sh        # Terraform installation
├── Development & Build
│   ├── check_terraform.sh          # Terraform validation
│   ├── ecr-login.sh                # ECR authentication
│   └── fix_and_apply.sh            # Terraform fix and apply
├── Deployment & Operations
│   ├── cleanup.sh                  # Full environment cleanup
│   ├── cleanup_ecs_services.sh     # ECS service cleanup
│   ├── ecs_force_cleanup.sh        # Force ECS cleanup
│   ├── ecs-alb-health.sh          # ALB health check
│   └── reset_env.sh                # Environment reset
├── IoT & Testing
│   ├── monitor_ven.py              # VEN monitoring
│   ├── send_event.py               # Send test events
│   ├── ven_acks_listen.py          # Listen for VEN acks
│   ├── ven_cmd_publish.py          # Publish VEN commands
│   ├── ven_http_live.py            # VEN HTTP monitoring
│   └── ven_shadow_get.py           # Get VEN shadow state
```

## Infrastructure & Setup Scripts

### AWS Authentication (`authenticate_aws.sh`)

Authenticates with AWS using SSO and sets up credentials.

#### Usage
```bash
# Basic SSO login
./scripts/authenticate_aws.sh

# With specific profile
AWS_PROFILE=AdministratorAccess-923675928909 ./scripts/authenticate_aws.sh
```

#### Environment Variables
- `AWS_PROFILE`: AWS profile name (default: `AdministratorAccess-923675928909`)
- `AWS_REGION`: AWS region (default: `us-west-2`)

#### Example Output
```
Starting AWS SSO login...
Successfully logged into AWS SSO
Setting default region to us-west-2
AWS credentials configured successfully
```

### Terraform State Bootstrap (`bootstrap_state.sh`)

Creates S3 bucket and DynamoDB table for Terraform remote state management.

#### Usage
```bash
# Create state resources in default region
./scripts/bootstrap_state.sh

# Create in specific region
AWS_REGION=us-east-1 ./scripts/bootstrap_state.sh
```

#### Created Resources
- **S3 Bucket**: `tf-state-<account-id>` (with versioning and encryption)
- **DynamoDB Table**: `tf-lock-<account-id>` (for state locking)

#### Environment Variables
- `AWS_REGION`: Target AWS region (default: `us-west-2`)
- `AWS_ACCOUNT_ID`: AWS account ID (auto-detected if not set)

#### Example
```bash
# Bootstrap state in us-east-1
AWS_REGION=us-east-1 ./scripts/bootstrap_state.sh

# Output:
# Creating Terraform state bucket: tf-state-123456789012
# Creating Terraform lock table: tf-lock-123456789012
# State management resources created successfully
```

### Package Installation Scripts

#### AWS CLI Installation (`install_awscli.sh`)
```bash
./scripts/install_awscli.sh

# Installs AWS CLI v2 and verifies installation
# Works on Linux (x86_64 and arm64) and macOS
```

#### Docker Installation (`install_docker.sh`)
```bash
./scripts/install_docker.sh

# Installs Docker CE and Docker Compose
# Adds current user to docker group
# Starts and enables Docker service
```

#### Terraform Installation (`install_terraform.sh`)
```bash
./scripts/install_terraform.sh

# Downloads and installs latest Terraform
# Verifies installation with version check
```

## Development & Build Scripts

### Terraform Validation (`check_terraform.sh`)

Validates and formats all Terraform files in the repository.

#### Usage
```bash
# Check all Terraform files
./scripts/check_terraform.sh

# Check specific directory
./scripts/check_terraform.sh envs/dev/
```

#### Operations Performed
1. **Format Check**: `terraform fmt -check -recursive`
2. **Validation**: `terraform validate` for each module
3. **Security Scan**: `checkov` security analysis (if available)

#### Example Output
```
Checking Terraform formatting...
✓ All files are properly formatted

Validating Terraform modules...
✓ modules/vpc: Valid
✓ modules/ecs-cluster: Valid
✓ modules/alb: Valid
✓ envs/dev: Valid

Running security checks...
✓ No security issues found

All Terraform checks passed!
```

### ECR Authentication (`ecr-login.sh`)

Authenticates Docker with Amazon ECR for image pushing/pulling.

#### Usage
```bash
# Login to ECR in default region
./scripts/ecr-login.sh

# Login with specific profile
AWS_PROFILE=my-profile ./scripts/ecr-login.sh

# Login to specific region
AWS_REGION=us-east-1 ./scripts/ecr-login.sh
```

#### Environment Variables
- `AWS_PROFILE`: AWS profile (default: `AdministratorAccess-923675928909`)
- `AWS_REGION`: AWS region (default: `us-west-2`)

#### Example
```bash
./scripts/ecr-login.sh
# Output: Login Succeeded to <account-id>.dkr.ecr.us-west-2.amazonaws.com
```

### Terraform Fix and Apply (`fix_and_apply.sh`)

Comprehensive Terraform workflow that formats, validates, and applies changes.

#### Usage
```bash
# Run from environment directory
cd envs/dev
../../scripts/fix_and_apply.sh

# Or specify target directory
./scripts/fix_and_apply.sh envs/dev/
```

#### Operations
1. Format all Terraform files
2. Validate configuration
3. Run security checks
4. Initialize Terraform
5. Plan changes
6. Apply with approval

## Deployment & Operations Scripts

### Environment Cleanup (`cleanup.sh`)

Safely destroys all Terraform-managed resources in an environment.

#### Usage
```bash
# Cleanup from environment directory
cd envs/dev
../../scripts/cleanup.sh

# Cleanup specific environment
./scripts/cleanup.sh envs/dev/
```

#### Safety Features
- Interactive confirmation required
- Terraform state backup before destruction
- Resource dependency validation

### ECS Service Management

#### ECS Service Cleanup (`cleanup_ecs_services.sh`)
```bash
# Clean up all ECS services
./scripts/cleanup_ecs_services.sh

# Clean up specific cluster
./scripts/cleanup_ecs_services.sh grid-services-dev
```

#### Force ECS Cleanup (`ecs_force_cleanup.sh`)
```bash
# Force cleanup stuck ECS services
./scripts/ecs_force_cleanup.sh

# This script:
# - Stops all running tasks
# - Scales services to 0
# - Deletes services
# - Removes task definitions
```

#### ALB Health Check (`ecs-alb-health.sh`)
```bash
# Check ALB and target health
./scripts/ecs-alb-health.sh

# Sample output:
# ALB Status: active
# Target Group: healthy
# Registered Targets: 2
# Healthy Targets: 2
```

### Environment Reset (`reset_env.sh`)

Complete environment reset - destroys and recreates infrastructure.

#### Usage
```bash
cd envs/dev
../../scripts/reset_env.sh

# This will:
# 1. Run cleanup.sh
# 2. Wait for confirmation
# 3. Run terraform_init.sh
# 4. Apply new infrastructure
```

## IoT & Testing Scripts

### VEN Command Publishing (`ven_cmd_publish.py`)

Publishes commands to VEN devices via AWS IoT Core.

#### Usage
```bash
# Set runtime configuration
./scripts/ven_cmd_publish.py \
  --ven-id $THING_NAME \
  --endpoint $IOT_ENDPOINT \
  --op setConfig \
  --data '{"report_interval_seconds": 30, "target_power_kw": 1.2}' \
  --corr-id cfg-1

# Update load configuration
./scripts/ven_cmd_publish.py \
  --ven-id $THING_NAME \
  --endpoint $IOT_ENDPOINT \
  --op setLoad \
  --data '{"loadId": "hvac1", "enabled": true, "capacityKw": 3.5}' \
  --corr-id load-1

# Send demand response event
./scripts/ven_cmd_publish.py \
  --ven-id $THING_NAME \
  --endpoint $IOT_ENDPOINT \
  --op event \
  --data '{"event_id": "evt-200", "start_ts": 1697034000, "duration_s": 600, "requestedReductionKw": 1.0}' \
  --corr-id ev-200

# Simple ping
./scripts/ven_cmd_publish.py \
  --ven-id $THING_NAME \
  --endpoint $IOT_ENDPOINT \
  --op ping
```

#### Command Operations
- `setConfig`: Update VEN runtime configuration
- `setLoad`: Configure individual load parameters
- `shedLoad`: Request load shedding
- `shedPanel`: Request panel-level shedding
- `get`: Request status/config/loads data
- `event`: Send demand response event
- `ping`: Connectivity test

#### Required Environment Variables
- `IOT_ENDPOINT`: AWS IoT Core endpoint
- `AWS_REGION`: AWS region (default: `us-west-2`)

### VEN Acknowledgment Listener (`ven_acks_listen.py`)

Listens for VEN acknowledgments and responses via WebSocket.

#### Usage
```bash
# Listen for acks from specific VEN
./scripts/ven_acks_listen.py \
  --ven-id $THING_NAME \
  --endpoint $IOT_ENDPOINT

# Listen with custom timeout
./scripts/ven_acks_listen.py \
  --ven-id $THING_NAME \
  --endpoint $IOT_ENDPOINT \
  --timeout 60
```

#### Example Output
```json
{
  "timestamp": "2023-10-11T15:30:00Z",
  "correlationId": "cfg-1",
  "venId": "ven-device-001",
  "status": "success",
  "message": "Configuration updated successfully"
}
```

### VEN HTTP Monitoring (`ven_http_live.py`)

Polls VEN HTTP endpoints for real-time status monitoring.

#### Usage
```bash
# Poll live endpoint every 2 seconds
./scripts/ven_http_live.py \
  --base-url $VEN_URL \
  --interval 2

# Poll with custom endpoint
./scripts/ven_http_live.py \
  --base-url https://sim.gridcircuit.link \
  --endpoint /circuits \
  --interval 5
```

#### Sample Output
```json
{"ok": true, "power_kw": 2.3, "shed_kw": 0.7, "event_status": "active", "event": "evt-200"}
{"ok": true, "power_kw": 2.1, "shed_kw": 0.9, "event_status": "active", "event": "evt-200"}
```

### VEN Shadow State (`ven_shadow_get.py`)

Retrieves and displays AWS IoT Thing Shadow state.

#### Usage
```bash
# Get full shadow state
./scripts/ven_shadow_get.py \
  --ven-id $THING_NAME \
  --endpoint $IOT_ENDPOINT

# Get only reported state
./scripts/ven_shadow_get.py \
  --ven-id $THING_NAME \
  --endpoint $IOT_ENDPOINT \
  --state-type reported

# Get only desired state
./scripts/ven_shadow_get.py \
  --ven-id $THING_NAME \
  --endpoint $IOT_ENDPOINT \
  --state-type desired
```

#### Example Output
```json
{
  "state": {
    "reported": {
      "ven": {
        "connected": true,
        "version": "1.0.0",
        "last_heartbeat": "2023-10-11T15:30:00Z"
      },
      "loads": {
        "hvac1": {"enabled": true, "power_kw": 2.1},
        "ev1": {"enabled": false, "power_kw": 0.0}
      },
      "metrics": {
        "total_power_kw": 2.1,
        "shed_kw": 0.9
      }
    }
  }
}
```

### Test Event Scripts

#### Send Test Event (`send_event.py`)
```bash
# Send basic test event
./scripts/send_event.py ven-device-001 --port 8883

# Send custom event
./scripts/send_event.py ven-device-001 \
  --port 8883 \
  --event-id "test-event-123" \
  --reduction-kw 2.5 \
  --duration 1800
```

#### Monitor VEN (`monitor_ven.py`)
```bash
# Monitor VEN responses
./scripts/monitor_ven.py ven-device-001 --port 8883

# Monitor with TLS
./scripts/monitor_ven.py ven-device-001 \
  --port 8883 \
  --ca-cert /path/to/ca.crt \
  --client-cert /path/to/client.crt \
  --client-key /path/to/client.key
```

## Script Configuration

### Environment Variables

#### Global Configuration
```bash
# AWS Configuration
export AWS_PROFILE=AdministratorAccess-923675928909
export AWS_REGION=us-west-2
export AWS_ACCOUNT_ID=123456789012

# IoT Configuration
export IOT_ENDPOINT=a1mgxpe8mg484j-ats.iot.us-west-2.amazonaws.com
export THING_NAME=ven-device-001

# Service URLs
export VEN_URL=https://sim.gridcircuit.link
export BACKEND_URL=https://api.gridcircuit.link

# Certificate Paths (for MQTT TLS)
export CA_CERT=/path/to/ca.crt
export CLIENT_CERT=/path/to/client.crt
export PRIVATE_KEY=/path/to/client.key
```

#### Script-Specific Configuration
```bash
# Terraform scripts
export TF_VAR_prefix=dev
export TF_VAR_aws_region=us-west-2

# ECS scripts
export CLUSTER_NAME=grid-services-dev
export SERVICE_NAME=backend-service

# Monitoring scripts
export POLL_INTERVAL=5
export TIMEOUT=30
```

### Common Script Patterns

#### Error Handling
```bash
#!/bin/bash
set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Function for error handling
error_exit() {
    echo "ERROR: $1" >&2
    exit 1
}

# Usage
aws sts get-caller-identity > /dev/null || error_exit "AWS credentials not configured"
```

#### Logging
```bash
# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

# Usage
log "Starting deployment process..."
log "Deployment completed successfully"
```

#### Confirmation Prompts
```bash
# Confirmation function
confirm() {
    read -p "$1 (y/N): " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]]
}

# Usage
if confirm "This will destroy all resources. Continue?"; then
    terraform destroy
fi
```

## Automation and Integration

### CI/CD Integration

#### GitHub Actions Usage
```yaml
# .github/workflows/deploy.yml
- name: Run Terraform validation
  run: ./scripts/check_terraform.sh

- name: Authenticate with ECR
  run: ./scripts/ecr-login.sh

- name: Deploy services
  run: |
    cd envs/dev
    ../../scripts/fix_and_apply.sh
```

#### Makefile Integration
```makefile
# Makefile
.PHONY: validate deploy clean

validate:
	./scripts/check_terraform.sh

deploy: validate
	cd envs/dev && ../../scripts/fix_and_apply.sh

clean:
	./scripts/cleanup.sh envs/dev/

test-ven:
	./scripts/ven_cmd_publish.py --ven-id $(THING_NAME) --op ping
```

### Monitoring Scripts

#### Health Check Script
```bash
#!/bin/bash
# scripts/health_check_all.sh

set -e

# Check all service endpoints
services=(
    "Backend:https://api.gridcircuit.link/health"
    "VEN:https://sim.gridcircuit.link/health"
    "VTN:https://vtn.gridcircuit.link/health"
)

for service in "${services[@]}"; do
    name="${service%%:*}"
    url="${service#*:}"
    
    if curl -f -s "$url" > /dev/null; then
        echo "✓ $name: Healthy"
    else
        echo "✗ $name: Unhealthy"
    fi
done
```

#### Deployment Status Script
```bash
#!/bin/bash
# scripts/deployment_status.sh

# Get ECS service status
aws ecs describe-services \
  --cluster grid-services-dev \
  --services backend-service volttron-service \
  --query 'services[].{Name:serviceName,Status:status,Running:runningCount,Desired:desiredCount}'

# Get ALB target health
aws elbv2 describe-target-health \
  --target-group-arn $(terraform output -raw target_group_arn) \
  --query 'TargetHealthDescriptions[].{Target:Target.Id,Health:TargetHealth.State}'
```

## Script Development Guidelines

### Best Practices

1. **Shebang and Set Options**:
   ```bash
   #!/bin/bash
   set -euo pipefail
   ```

2. **Help and Usage**:
   ```bash
   usage() {
       cat << EOF
   Usage: $0 [OPTIONS]
   
   Description of what the script does.
   
   OPTIONS:
       -h, --help      Show this help message
       -v, --verbose   Enable verbose output
   EOF
   }
   ```

3. **Argument Parsing**:
   ```bash
   while [[ $# -gt 0 ]]; do
       case $1 in
           -h|--help)
               usage
               exit 0
               ;;
           -v|--verbose)
               VERBOSE=1
               shift
               ;;
           *)
               echo "Unknown option: $1"
               usage
               exit 1
               ;;
       esac
   done
   ```

4. **Environment Variable Defaults**:
   ```bash
   AWS_REGION="${AWS_REGION:-us-west-2}"
   CLUSTER_NAME="${CLUSTER_NAME:-grid-services-dev}"
   ```

### Testing Scripts

```bash
# Test script functionality
./scripts/test_all.sh

# Validate script syntax
shellcheck scripts/*.sh

# Test with different environments
AWS_REGION=us-east-1 ./scripts/bootstrap_state.sh
```

This comprehensive scripts reference provides all the information needed to understand, use, and maintain the automation tools in the Grid Services repository.