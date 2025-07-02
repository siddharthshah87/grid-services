#!/usr/bin/env bash
set -euo pipefail

: "${AWS_PROFILE?Must set AWS_PROFILE to your AWS profile name}"
: "${TF_STATE_BUCKET?Must set TF_STATE_BUCKET to your S3 backend bucket}"

REGION="${AWS_REGION:-us-west-2}"

terraform init -reconfigure \
  -backend-config="bucket=${TF_STATE_BUCKET}" \
  -backend-config="key=dev/terraform.tfstate" \
  -backend-config="region=${REGION}" \
  -backend-config="use_lockfile=true" \
  -backend-config="encrypt=true"
terraform workspace select dev || terraform workspace new dev
terraform plan
terraform apply

