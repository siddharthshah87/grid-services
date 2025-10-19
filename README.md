
# Grid Services Infrastructure

This repository contains Terraform modules and applications to deploy a demand response (DR) system on AWS with a local Virtual End Node (VEN) for testing.

## Repository Structure

- `envs/` – Terraform environments. The `dev` folder provisions the required AWS resources.
- `modules/` – Reusable Terraform modules (VPC, ECS cluster, ECR repositories, security groups, IAM roles, IoT Core and more).
- `volttron-ven/` – Local VEN implementation with DR event handling and web UI.
- `ecs-backend/` – FastAPI backend providing the administration API and event command service.
- `ecs-frontend/` – React/Vite frontend dashboard.
- `scripts/` – Helper scripts for infrastructure, deployment, and VEN control.
- `docs/` – Comprehensive documentation for architecture, operations, and testing.
- `.github/workflows/` – GitHub Actions pipelines for linting, testing, and security scanning.

See `docs/VEN_OPERATIONS.md` for VEN operations and `docs/testing.md` for end-to-end testing.

## Prerequisites

- **AWS account** with permissions to create the resources described in `envs/dev`.
- **Docker** – install via `scripts/install_docker.sh` or from the [official instructions](https://docs.docker.com/get-docker/).
- **AWS CLI** – install via `scripts/install_awscli.sh`.
- **Terraform** – install via `scripts/install_terraform.sh`.

Ensure your shell has access to AWS credentials. The provided script `scripts/authenticate_aws.sh` uses AWS SSO to log in.

## Bootstrapping Terraform State

Before applying Terraform, create an S3 bucket and DynamoDB table for remote state and locking. Run:

```bash
./scripts/bootstrap_state.sh
```

This script uses your current AWS credentials to create a bucket named `tf-state-<account-id>` and a DynamoDB table named `tf-lock-<account-id>` in region `us-west-2` by default. Set `AWS_REGION` to override the target region.

## Building and Pushing Docker Images

1. Authenticate Docker to your ECR registry:

   ```bash
   ./scripts/ecr-login.sh
   ```

2. Build and push the ECS Backend image:

   ```bash
   cd ecs-backend
   ./build_and_push.sh
   cd ..
   ```

3. Build and push the frontend dashboard image. Optionally set
   `BACKEND_API_URL` to inject the backend endpoint during the build:

   ```bash
   cd ecs-frontend
   ./build_and_push.sh
   cd ..
   ```

**Note**: The VEN runs locally (not containerized). See `docs/VEN_OPERATIONS.md` for VEN setup.

The scripts obtain your AWS account ID automatically and push the `latest` tag to ECR. Set
`AWS_PROFILE` to use a different credentials profile (defaults to `AdministratorAccess-923675928909`).

## Deploying the Development Environment

From the repository root:

```bash
cd envs/dev
./terraform_init.sh        # initializes the workspace and applies the configuration
```

This environment creates:

- A VPC with public subnets
- ECR repositories for backend and frontend images
- An IoT Core thing, policy and certificates for VEN
- An ECS cluster and related IAM roles
- Fargate services for backend and frontend
- Application Load Balancers for backend and frontend
- An IoT topic rule forwarding telemetry to S3 bucket `mqtt-forward-mqtt-logs` and Kinesis stream `mqtt-forward-mqtt-stream`
- RDS PostgreSQL database for backend data storage

Adjust variables and module parameters in `envs/dev/main.tf` as needed (e.g., MQTT topic or IoT endpoint).

### Capturing IoT Certificates

The IoT Core module outputs the certificate and key needed for MQTT TLS. After
`terraform apply` run:

```bash
terraform output -raw certificate_pem > client.crt
terraform output -raw private_key > client.key
```

Use these outputs directly when setting the environment variables for the
VTN and VEN services:

```bash
export CLIENT_CERT=$(terraform output -raw certificate_pem)
export PRIVATE_KEY=$(terraform output -raw private_key)
export CA_CERT=$CLIENT_CERT
```

OpenSSL is not required as AWS IoT generates the certificate and private key
for you.

### Working with the AWS IoT device shadow

The IoT Core module exports the thing name as the `thing_name` output and the
Volttron ECS task now injects this value into the VEN container via the
`IOT_THING_NAME` environment variable (the Docker Compose definition accepts
the same variable for local testing). When this variable is present the VEN:

- Publishes its current status, metering sample and reporting interval to the
  thing shadow’s `state.reported` document.
- Subscribes to `$aws/things/<thing>/shadow/update/delta`, applies recognised
  fields such as `report_interval_seconds` and `target_power_kw`, then writes
  the acknowledged values back to `state.reported` so the delta is cleared.
- Requests the current shadow document on start-up so any stored desired state
  is honoured immediately.

Use the AWS CLI (v2) to exercise the behaviour once Terraform has been
applied:

```bash
export THING_NAME=$(terraform output -raw thing_name)

# Push a desired-state change (e.g. faster reporting and a 1.2 kW target)
aws iot-data update-thing-shadow \
  --region us-west-2 \
  --thing-name "$THING_NAME" \
  --cli-binary-format raw-in-base64-out \
  --payload '{"state":{"desired":{"report_interval_seconds":5,"target_power_kw":1.2}}}' \
  update-response.json

# Retrieve the VEN's reported shadow document
aws iot-data get-thing-shadow \
  --region us-west-2 \
  --thing-name "$THING_NAME" \
  shadow.json

jq -r '.state.reported' shadow.json
```

The CLI commands above save the responses to files (`update-response.json` and
`shadow.json`) so you can inspect the JSON returned by IoT Core. Changing
`report_interval_seconds` alters how frequently the VEN publishes and
`target_power_kw` adjusts the centre point of the simulated metering data. You
can still override the default interval locally by setting the
`VEN_REPORT_INTERVAL_SECONDS` environment variable if you do not want to rely
on the shadow.

### Querying MQTT Logs

After applying Terraform, the rule outputs the S3 bucket and Kinesis stream
used for message capture. Retrieve their names with:

```bash
terraform output log_bucket_name
terraform output log_stream_name
```

To inspect the S3 objects:

```bash
aws s3 ls s3://$(terraform output -raw log_bucket_name)/ --recursive
```

To read records from the Kinesis stream:

```bash
aws kinesis get-records \
  --shard-iterator $(aws kinesis get-shard-iterator \
    --stream-name $(terraform output -raw log_stream_name) \
    --shard-id shardId-000000000000 \
    --shard-iterator-type TRIM_HORIZON \
    --query ShardIterator --output text) \
  --limit 10
```

## Cleaning Up

To destroy all resources created in the `dev` environment:

```bash
terraform destroy
```

Run this inside the `envs/dev` directory with the same workspace selected.

### Using `scripts/cleanup.sh`

If you only want to remove the running containers and other high-cost
resources while keeping the VPC, ECR repositories and IAM roles, use the
`scripts/cleanup.sh` helper.

**Prerequisites**

- The `dev` environment has been deployed (e.g. via `./terraform_init.sh`).
- You are inside the `envs/dev` directory so Terraform can find its state.
- The correct workspace (such as `dev`) is selected.

Run the script whenever you are done testing and want to stop incurring
compute costs but may redeploy later:

```bash
cd envs/dev
../../scripts/cleanup.sh
```

Re-running `terraform apply` will recreate the services when needed.

## Additional Notes

- The Terraform configuration requires version `>= 1.8.0` and the AWS provider `~> 5.40` as defined in `envs/dev/versions.tf`.
- GitHub Actions workflows automatically lint, test, scan for vulnerabilities and generate Terraform plans on pull requests.
- Run `scripts/check_terraform.sh` before committing to ensure Terraform files are formatted and valid.
- The container applications connect to MQTT on port `8883` by default. Set the
  environment variables `CA_CERT`, `CLIENT_CERT`, and `PRIVATE_KEY` (or the
  `_PEM`-suffixed variants) with the paths or PEM contents for your broker's
  certificate authority, client certificate and key to enable TLS.
- The applications default to the AWS IoT Core ATS data endpoint exported by
  Terraform. When the services run behind the VPC interface endpoint,
  Terraform also sets `IOT_CONNECT_HOST` to the private DNS name and
  `IOT_TLS_SERVER_NAME` to the public IoT endpoint so TLS hostname checks still
  succeed. Override these environment variables if you run the containers
  outside this infrastructure.
- Set `IOT_THING_NAME` so the VEN synchronises with the AWS IoT device shadow.
  Terraform wires this value into the ECS task definition automatically and the
  Docker Compose file exposes the same variable for local runs. Override the
  default reporting cadence without touching the shadow by setting
  `VEN_REPORT_INTERVAL_SECONDS`.
- The container applications are minimal examples. Customize `grid-event-gateway/vtn_server.py` and `volttron-ven/ven_agent.py` for your use case.

## Grid-Event Gateway

The `grid-event-gateway/vtn_server.py` script provides a minimal VTN for testing. The
server listens on port `8080` for OpenADR traffic. It now tracks the VENs that
register with it and exposes a simple HTTP endpoint to list them. The
listing server's port can be configured via the `VENS_PORT` environment
variable (default `8081`).

### Listing active VENs

Run the server and then access `http://localhost:8081/vens` (or the port you
set in `VENS_PORT`) to retrieve a JSON array of currently registered VEN
IDs.


## Demo

Two helper scripts allow quick testing of the MQTT topics used by the VTN and
VEN examples. Set the environment variables before running them:

```bash
export IOT_ENDPOINT=a1mgxpe8mg484j-ats.iot.us-west-2.amazonaws.com
# For MQTT over TLS also set the certificate paths
export CA_CERT=/path/to/ca.pem
export CLIENT_CERT=/path/to/client.crt
export PRIVATE_KEY=/path/to/client.key
# When using a private IoT VPC endpoint also set:
# export IOT_CONNECT_HOST=your-private-endpoint.amazonaws.com
# export IOT_TLS_SERVER_NAME=a1234567890-ats.iot.us-west-2.amazonaws.com
```

Use `--port 8883` when connecting with TLS (otherwise the default `1883` is
used).

1. Start monitoring responses for a VEN:

```bash
python scripts/monitor_ven.py ven123 --port 8883
```

2. In another terminal send a test event:

```bash
python scripts/send_event.py ven123 --port 8883
```

The monitor subscribes to `grid/response/ven123` and prints any messages. The
sender publishes a simple event to `grid/event/ven123`.

## Running Locally with Docker Compose

You can bring up the VTN and VEN containers without deploying any AWS
infrastructure. Place your MQTT/TLS certificates in a `certs/` directory at the
repository root:

```
certs/
  ca.crt
  client.crt
  client.key
```

Set the required environment variables for your broker endpoint and topics (or
create a `.env` file) and then start the stack:

```bash
docker compose up
```

The Grid-Event Gateway will be available on port `8080` with the VEN listing endpoint on
`8081`.


# AWS-VAULT
On ubuntu 
sudo apt install aws-vault

aws-vault exec AdministratorAccess-923675928909 -- ./terraform_init.sh

## Running Tests

To run the unit tests locally install the required Python packages and execute
`pytest`. Terraform must also be installed so that `scripts/check_terraform.sh`
can validate the configuration.

```bash
pip install -r grid-event-gateway/requirements.txt -r volttron-ven/requirements.txt \
  fastapi uvicorn sqlalchemy asyncpg alembic python-dotenv \
  pydantic pydantic-settings sqlmodel httpx pytest pytest-asyncio \
  aiosqlite paho-mqtt pyOpenSSL==22.1.0
export PYTHONPATH=ecs-backend
./scripts/check_terraform.sh
pytest
```

# TLDR
## Deploy Infra
```bash
cd envs/dev
./terraform_init.sh
```
## Build & Deploy Services 
```bash
# Backend
cd ecs-backend && ./build_and_push.sh

# Frontend  
cd ecs-frontend && ./build_and_push.sh

# Redeploy both
./redeploy_service.sh
```

## Run VEN Locally
./scripts/ven_control.sh start
./scripts/ven_control.sh send-event --shed-kw 2.0 --duration 300
./scripts/ven_control.sh restore
./scripts/ven_control.sh stop
