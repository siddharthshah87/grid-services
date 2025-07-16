#!/usr/bin/env bash
set -euo pipefail

PROFILE="${AWS_PROFILE:-AdministratorAccess-923675928909}"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text --profile "$PROFILE")
REGION="${AWS_REGION:-us-west-2}"
REPO_URI="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/ecs-frontend"

aws ecr get-login-password --region "$REGION" --profile "$PROFILE" | docker login --username AWS --password-stdin "$REPO_URI"

BUILD_ARGS=""
if [ -n "${BACKEND_API_URL:-}" ]; then
  BUILD_ARGS="--build-arg BACKEND_API_URL=$BACKEND_API_URL"
fi

docker build $BUILD_ARGS -t ecs-frontend .
docker tag ecs-frontend:latest "$REPO_URI:latest"
docker push "$REPO_URI:latest"
