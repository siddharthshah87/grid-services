#!/usr/bin/env bash
set -euo pipefail
AWS_PROFILE="AdministratorAccess-923675928909"
REGION="us-west-2"
AWS_DEFAULT_REGION="us-west-2"
CLUSTER="hems-ecs-cluster"

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🚀 Bringing up the full development environment..."

cd "$REPO_DIR/envs/dev"

# Optional: Re-import resources if needed (only run this if your state was wiped)
./terraform_import.sh

# Initialize and apply the infra
./terraform_init.sh

# Build and push the Docker images for all services
cd "$REPO_DIR/openleadr"
./build_and_push.sh

cd "$REPO_DIR/openadr_backend"
./build_and_push.sh

cd "$REPO_DIR/ecs-frontend"
./build_and_push.sh

cd "$REPO_DIR/volttron"
./build_and_push.sh

for svc in openadr-backend openleadr-vtn volttron-ven ecs-frontend; do
  echo "🔁 Forcing redeploy of $svc"
  aws ecs update-service \
    --cluster "$CLUSTER" \
    --service "$svc" \
    --force-new-deployment \
    --region "$REGION" \
    --profile "$AWS_PROFILE" || true
done

echo "✅ Environment is up. All services should be running."

