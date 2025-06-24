# openleadr/build_and_push.sh
#!/usr/bin/env bash
set -euo pipefail

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=us-west-1
REPO_URI="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/openleadr-vtn"

echo "Building and pushing to $REPO_URI..."
docker build -t openleadr-vtn .
docker tag openleadr-vtn:latest "$REPO_URI:latest"
docker push "$REPO_URI:latest"
