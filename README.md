
# Grid Services Infrastructure

This repository contains Terraform modules and Dockerized applications to deploy an OpenADR VTN server and a Volttron VEN agent on AWS. It provides example configurations for a development environment and helper scripts for setting up prerequisites.

## Repository Structure

- `envs/` – Terraform environments. The `dev` folder is a working example that provisions the required AWS resources.
- `modules/` – Reusable Terraform modules (VPC, ECS cluster, ECR repositories, security groups, IAM roles, IoT Core and more).
- `openleadr/` – Source code and Dockerfile for the [OpenLEADR](https://github.com/OpenLEADR/openleadr) VTN server.
- `volttron/` – Source code and Dockerfile for a simple Volttron VEN agent.
- `scripts/` – Helper scripts to install dependencies, authenticate to AWS, create Terraform backend resources and push Docker images.
- `ci/` – GitHub Actions workflows for formatting and planning Terraform changes.

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

2. Build and push the OpenLEADR VTN image:

   ```bash
   cd openleadr
   ./build_and_push.sh
   cd ..
   ```

3. Build and push the Volttron VEN image:

   ```bash
   cd volttron
   ./build_and_push.sh
   cd ..
   ```

The scripts obtain your AWS account ID automatically and push the `latest` tag to ECR.

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

Adjust variables and module parameters in `envs/dev/main.tf` as needed (e.g., MQTT topic or IoT endpoint).

## Cleaning Up

To destroy all resources created in the `dev` environment:

```bash
terraform destroy
```

Run this inside the `envs/dev` directory with the same workspace selected.

## Additional Notes

- The Terraform configuration requires version `>= 1.8.0` and the AWS provider `~> 5.40` as defined in `envs/dev/versions.tf`.
- GitHub Actions workflows under `ci/` will format Terraform code and perform planning on pull requests.
- The container applications are minimal examples. Customize `openleadr/vtn_server.py` and `volttron/ven_agent.py` for your use case.

## OpenADR VTN

The `openleadr/vtn_server.py` script provides a minimal VTN for testing. The
server listens on port `8080` for OpenADR traffic. It now tracks the VENs that
register with it and exposes a simple HTTP endpoint to list them.

### Listing active VENs

Run the server and then access `http://localhost:8081/vens` to retrieve a JSON
array of currently registered VEN IDs.

