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
# Default backend API if not provided
if [[ -z "${BACKEND_API_URL:-}" ]]; then
  DEFAULT_BACKEND_API_URL="http://backend-alb-948465488.us-west-2.elb.amazonaws.com"
  echo "BACKEND_API_URL not provided. Using default: $DEFAULT_BACKEND_API_URL"
  BACKEND_API_URL="$DEFAULT_BACKEND_API_URL"
else
  echo "Using BACKEND_API_URL: $BACKEND_API_URL"
fi

BUILD_ARGS+=(--build-arg "BACKEND_API_URL=$BACKEND_API_URL")

# Build & push in one go
docker build \
  "${BUILD_ARGS[@]}" \
  -t "$REPO_URI" \
  .

docker push "$REPO_URI"
