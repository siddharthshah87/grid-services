#!/usr/bin/env bash
set -euo pipefail

# Defaults (override via env)
PROFILE="${AWS_PROFILE:-AdministratorAccess-923675928909}"
REGION="${AWS_REGION:-us-west-2}"
ACCOUNT_ID=$(aws sts get-caller-identity \
  --query Account --output text --profile "$PROFILE")
REPO_URI="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/ecs-frontend:latest"

# Log into ECR
aws ecr get-login-password \
  --region "$REGION" \
  --profile "$PROFILE" \
| docker login --username AWS --password-stdin "${REPO_URI%/*}"

# Build args
BUILD_ARGS=()
if [[ -n "${BACKEND_API_URL:-}" ]]; then
  BUILD_ARGS+=(--build-arg "BACKEND_API_URL=$BACKEND_API_URL")
fi

# Build & push in one go
docker build \
  "${BUILD_ARGS[@]}" \
  -t "$REPO_URI" \
  .

docker push "$REPO_URI"

