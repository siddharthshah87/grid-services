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

REPO_URI="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/ecs-backend"
eval "$LOGIN_CMD" | docker login --username AWS --password-stdin "$REPO_URI"

cd "$(dirname "$0")"

echo "🐳 Building Docker image..."
docker build -t ecs-backend .

echo "🏷️ Tagging and pushing to $REPO_URI..."
docker tag ecs-backend:latest "$REPO_URI:latest"
docker push "$REPO_URI:latest"

echo "✅ Done. Image pushed to $REPO_URI:latest"

