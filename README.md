
# Grid Services Infrastructure

This repository contains Terraform modules and Dockerized applications to deploy an OpenADR VTN server and a Volttron VEN agent on AWS. It provides example configurations for a development environment and helper scripts for setting up prerequisites.

## Repository Structure

- `envs/` – Terraform environments. The `dev` folder is a working example that provisions the required AWS resources.
- `modules/` – Reusable Terraform modules (VPC, ECS cluster, ECR repositories, security groups, IAM roles, IoT Core and more).
- `grid-event-gateway/` – Source code and Dockerfile for the Grid-Event Gateway (OpenADR VTN) server.
- `volttron-ven/` – Source code and Dockerfile for a simple Volttron VEN agent.
- `ecs-backend/` – FastAPI backend providing the administration API.
- `scripts/` – Helper scripts to install dependencies, authenticate to AWS, create Terraform backend resources, push Docker images, and verify Terraform formatting.
- `.github/workflows/` – GitHub Actions pipelines for linting, testing, security scanning and Terraform operations.

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

2. Build and push the Grid-Event Gateway image:

   ```bash
   cd grid-event-gateway
   ./build_and_push.sh
   cd ..
   ```

3. Build and push the ECS Backend image:

   ```bash
   cd ecs-backend
   ./build_and_push.sh
   cd ..
   ```

4. Build and push the Volttron VEN image:

   ```bash
   cd volttron-ven
   ./build_and_push.sh
   cd ..
   ```

5. Build and push the frontend dashboard image. Optionally set
   `BACKEND_API_URL` to inject the backend endpoint during the build:

   ```bash
   cd ecs-frontend
   ./build_and_push.sh
   cd ..
   ```

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
- ECR repositories for the images above
- An IoT Core thing, policy and certificates
- An ECS cluster and related IAM roles
- Fargate services for the VTN and VEN containers
- An Application Load Balancer exposing the VTN on port 80
- An IoT topic rule logging messages to S3 bucket `mqtt-forward-mqtt-logs` and Kinesis stream `mqtt-forward-mqtt-stream`

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
- The container applications connect to MQTT on port `8883` by default. Set
  the environment variables `CA_CERT`, `CLIENT_CERT`, and `PRIVATE_KEY` with the
  paths to your broker's certificate authority, client certificate and key to
  enable TLS.
- By default the applications target the AWS IoT Core endpoint
  `vpce-0d3cb8ea5764b8097-r1j8w787.data.iot.us-west-2.vpce.amazonaws.com`. Set
  the `IOT_ENDPOINT` environment variable if you need to override this.
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
export IOT_ENDPOINT=vpce-0d3cb8ea5764b8097-r1j8w787.data.iot.us-west-2.vpce.amazonaws.com
# For MQTT over TLS also set the certificate paths
export CA_CERT=/path/to/ca.pem
export CLIENT_CERT=/path/to/client.crt
export PRIVATE_KEY=/path/to/client.key
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
