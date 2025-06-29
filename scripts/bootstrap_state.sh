#!/bin/bash

set -e

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION="${AWS_REGION:-us-west-2}"

STATE_BUCKET="tf-state-grid-services-${ACCOUNT_ID}"
LOCK_TABLE="tf-lock-${ACCOUNT_ID}"

echo "Creating state bucket: $STATE_BUCKET in $REGION"

aws s3api create-bucket \
  --bucket "$STATE_BUCKET" \
  --region "$REGION" \
  --create-bucket-configuration LocationConstraint="$REGION" || true

aws s3api put-bucket-versioning \
  --bucket "$STATE_BUCKET" \
  --versioning-configuration Status=Enabled

echo "Creating DynamoDB table: $LOCK_TABLE in $REGION"

aws dynamodb create-table \
  --table-name "$LOCK_TABLE" \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region "$REGION" || true

echo "✅ Bootstrap complete."

