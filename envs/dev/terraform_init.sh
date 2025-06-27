#!/usr/bin/env bash
set -euo pipefail

export AWS_PROFILE=AdministratorAccess-923675928909 

terraform init -reconfigure
terraform workspace select dev || terraform workspace new dev
terraform plan
terraform apply

