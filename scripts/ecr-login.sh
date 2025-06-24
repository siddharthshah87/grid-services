#!/usr/bin/env bash
set -euo pipefail

AWS_REGION="us-west-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "Logging in to ECR for account $ACCOUNT_ID in region $AWS_REGION..."

aws ecr get-login-password --region "$AWS_REGION" | \
docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

