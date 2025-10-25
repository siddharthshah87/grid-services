# Development Setup Guide

This guide covers setting up a local development environment for the Grid Services infrastructure, including both AWS-based and local Docker Compose workflows.

## Prerequisites

### System Requirements
- **Docker** and **Docker Compose** - for containerized development
- **Python 3.10+** - for running services locally
- **Node.js 18+** - for frontend development
- **Git** - for version control
- **AWS CLI** - for AWS resource interaction

### Installation Scripts
Use the provided installation scripts to set up dependencies:

```bash
# Install Docker
./scripts/install_docker.sh

# Install AWS CLI
./scripts/install_awscli.sh

# Install Terraform (for infrastructure work)
./scripts/install_terraform.sh
```

### AWS Credentials
Configure AWS access using one of these methods:

#### Option 1: AWS SSO (Recommended)
```bash
# Step 1: Get your SSO start URL from AWS administrator or:
# - AWS Console → IAM Identity Center → "AWS access portal URL"
# - Format: https://d-xxxxxxxxxx.awsapps.com/start

# Step 2: Configure SSO
aws configure sso
# You'll be prompted for:
# - SSO start URL: https://d-xxxxxxxxxx.awsapps.com/start
# - SSO region: us-west-2 (or your organization's region)
# - Account ID: 923675928909 (or your account)
# - Role name: AdministratorAccess-923675928909 (or your role)
# - Profile name: AdministratorAccess-923675928909

# Step 3: Login
aws sso login --profile AdministratorAccess-923675928909

# Step 4: Use the provided authentication script
./scripts/authenticate_aws.sh
```

#### Option 2: aws-vault (Alternative)
```bash
# Install aws-vault (Ubuntu)
sudo apt install aws-vault

# Use with Terraform commands
aws-vault exec AdministratorAccess-923675928909 -- ./terraform_init.sh
```

#### Option 3: Environment Variables
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-west-2
```

## Python Development Environment

### Virtual Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip setuptools wheel

# Install all development dependencies
pip install -r requirements-dev.txt

# For testing dependencies
pip install -r requirements-testing.txt

# For specific service development
pip install -r grid-event-gateway/requirements.txt
pip install -r volttron-ven/requirements.txt
pip install -r ecs-backend/requirements.txt
```

### Backend Development
```bash
# Set PYTHONPATH for backend development
export PYTHONPATH=ecs-backend

# Navigate to backend directory
cd ecs-backend

# Set required environment variables
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=grid_services
export DB_USER=postgres
export DB_PASSWORD=postgres

# Run database migrations
alembic upgrade head

# Start the FastAPI development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Local Development with Docker Compose

### Certificate Setup for MQTT
Create a `certs/` directory in the repository root and place your MQTT/TLS certificates:

```bash
mkdir -p certs
# Place your certificates:
# certs/ca.crt
# certs/client.crt  
# certs/client.key
```

### Environment Configuration
Create a `.env` file in the repository root:

```bash
# MQTT Configuration
IOT_ENDPOINT=your-iot-endpoint.amazonaws.com
MQTT_TOPIC_METERING=volttron/metering
MQTT_TOPIC_EVENTS=openadr/event
MQTT_TOPIC_RESPONSES=openadr/response

# Certificate paths (for Docker volumes)
CA_CERT=/certs/ca.crt
CLIENT_CERT=/certs/client.crt
PRIVATE_KEY=/certs/client.key

# Database Configuration
DB_HOST=db
DB_PORT=5432
DB_NAME=grid_services
DB_USER=postgres
DB_PASSWORD=postgres

# Optional: Custom ports
VTN_PORT=8080
VEN_PORT=8081
BACKEND_PORT=8000
FRONTEND_PORT=3000
```

### Starting the Development Stack
```bash
# Start all services
docker compose up

# Start specific services
docker compose up db backend frontend

# Start in background
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

### Service Access
Once running, services are available at:
- **Grid-Event Gateway (VTN)**: http://localhost:8080
- **VEN Agent**: http://localhost:8081
- **Backend API**: http://localhost:8000
- **Frontend**: http://localhost:3000
- **Database**: localhost:5432

## Individual Service Development

### VEN Agent Development
```bash
cd volttron-ven

# Set local development mode
export LOCAL_DEV=1

# Configure MQTT (for local broker)
export MQTT_HOST=localhost
export MQTT_PORT=1883
export MQTT_USE_TLS=false

# Or for AWS IoT Core
export MQTT_HOST=your-iot-endpoint.amazonaws.com
export MQTT_PORT=8883
export MQTT_USE_TLS=true
export CA_CERT=/path/to/ca.crt
export CLIENT_CERT=/path/to/client.crt
export PRIVATE_KEY=/path/to/client.key

# Set IoT Thing name
export IOT_THING_NAME=ven-dev-123

# Start the VEN agent
python ven_agent.py
```

### Grid-Event Gateway Development
```bash
cd grid-event-gateway

# Configure MQTT endpoint
export IOT_ENDPOINT=your-iot-endpoint.amazonaws.com
export VENS_PORT=8081

# Set certificate paths
export CA_CERT=/path/to/ca.crt
export CLIENT_CERT=/path/to/client.crt
export PRIVATE_KEY=/path/to/client.key

# Start the VTN server
python vtn_server.py
```

### Frontend Development
```bash
cd ecs-frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Database Setup

### Local PostgreSQL
```bash
# Using Docker
docker run --name postgres-dev \
  -e POSTGRES_DB=grid_services \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  -d postgres:15

# Or use the Docker Compose stack
docker compose up db
```

### Database Migrations
```bash
cd ecs-backend

# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migrations
alembic downgrade -1
```

## Testing

### Running Tests
```bash
# Run all tests
pytest

# Run specific test suites
pytest ecs-backend/tests/test_routers_ven.py  # VEN API tests
pytest ecs-backend/tests/test_service_*.py     # Service layer tests
pytest tests/test_contract_*.py                # MQTT contract tests

# Run with coverage
PYTHONPATH=ecs-backend pytest ecs-backend/tests/ --cov=app --cov-report=html

# Run tests in parallel
pytest -n auto
```

### Test Configuration
```bash
# Set test environment variables
export PYTEST_CURRENT_TEST=1
export DB_NAME=grid_services_test

# For MQTT testing
export MQTT_ENABLED=false
```

## Development Workflow

### Code Quality Checks
```bash
# Check Terraform formatting
./scripts/check_terraform.sh

# Run linting and tests (as CI does)
pytest
flake8 ecs-backend/app/
black --check ecs-backend/app/
isort --check-only ecs-backend/app/
```

### Building and Testing Docker Images
```bash
# Build all images
docker compose build

# Build specific service
docker compose build backend

# Test image builds
cd grid-event-gateway && docker build -t grid-event-gateway:dev .
cd volttron-ven && docker build -t volttron-ven:dev .
cd ecs-backend && docker build -t ecs-backend:dev .
cd ecs-frontend && docker build -t ecs-frontend:dev .
```

## Debugging and Troubleshooting

### Common Issues

#### Docker Compose Issues
```bash
# Clear containers and volumes
docker compose down -v

# Rebuild images without cache
docker compose build --no-cache

# Check service logs
docker compose logs backend
docker compose logs ven
```

#### Certificate Issues
```bash
# Verify certificate format
openssl x509 -in certs/client.crt -text -noout

# Test MQTT connection
mosquitto_pub -h your-endpoint.amazonaws.com -p 8883 \
  --cafile certs/ca.crt \
  --cert certs/client.crt \
  --key certs/client.key \
  -t test/topic -m "test message"
```

#### Database Issues
```bash
# Reset database
docker compose down -v
docker compose up db

# Check database connection
psql -h localhost -U postgres -d grid_services

# View migration status
cd ecs-backend && alembic current
```

### Development Tools

#### VS Code Configuration
Recommended extensions:
- Python
- Docker
- Terraform
- REST Client
- GitLens

#### Environment Variables
Use VS Code's `.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.terminal.activateEnvironment": true,
  "terraform.languageServer.enable": true
}
```

### Hot Reloading
- **Backend**: FastAPI auto-reloads with `--reload` flag
- **Frontend**: Vite provides hot module replacement
- **VEN/VTN**: Restart required for changes

## Next Steps

After setting up your development environment:

1. Review the [Testing Guide](testing.md) for end-to-end testing
2. Check [API Documentation](backend-api.md) for backend development
3. See [VEN Contract](ven-contract.md) for MQTT integration
4. Explore [Deployment Operations](deployment-operations.md) for AWS workflows

## Support

For development issues:
1. Check service logs: `docker compose logs <service>`
2. Verify environment variables are set correctly
3. Ensure certificates are valid and accessible
4. Check network connectivity to AWS services