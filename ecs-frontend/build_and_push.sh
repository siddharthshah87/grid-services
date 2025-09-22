#!/usr/bin/env bash
set -euo pipefail

REGION="${AWS_REGION:-us-west-2}"

if [ -n "${AWS_PROFILE:-}" ]; then
  ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text --profile "$AWS_PROFILE")
  LOGIN_CMD="aws ecr get-login-password --region \"$REGION\" --profile \"$AWS_PROFILE\""
else
  ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
  LOGIN_CMD="aws ecr get-login-password --region \"$REGION\""
fi

REPO_URI="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/ecs-frontend:latest"
eval "$LOGIN_CMD" | docker login --username AWS --password-stdin "$REPO_URI"

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

