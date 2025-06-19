#!/usr/bin/env bash
set -euo pipefail

export AWS_REGION=us-west-2   # adjust
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

BUCKET="tf-state-${ACCOUNT_ID}"
TABLE="tf-lock-${ACCOUNT_ID}"

aws s3api create-bucket --bucket "$BUCKET" --create-bucket-configuration LocationConstraint=$AWS_REGION
aws s3api put-bucket-versioning --bucket "$BUCKET" --versioning-configuration Status=Enabled

aws dynamodb create-table \
  --table-name "$TABLE" \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

