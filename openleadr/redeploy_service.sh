#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="openleadr-vtn"
CLUSTER_NAME="hems-ecs-cluster"
REGION="us-west-2"
PROFILE="AdministratorAccess-923675928909"
IMAGE_NAME="923675928909.dkr.ecr.${REGION}.amazonaws.com/${SERVICE_NAME}:latest"

echo "📦 Building updated image for $SERVICE_NAME..."
docker build -t "$IMAGE_NAME" .
aws ecr get-login-password --region "$REGION" --profile "$PROFILE" | docker login --username AWS --password-stdin "923675928909.dkr.ecr.${REGION}.amazonaws.com"
docker push "$IMAGE_NAME"

echo "🔁 Forcing ECS service redeploy for $SERVICE_NAME..."
aws ecs update-service \
  --cluster "$CLUSTER_NAME" \
  --service "$SERVICE_NAME" \
  --force-new-deployment \
  --region "$REGION" \
  --profile "$PROFILE"

echo "✅ $SERVICE_NAME redeploy triggered with latest image."

