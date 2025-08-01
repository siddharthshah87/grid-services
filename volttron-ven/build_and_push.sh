# volttron-ven/build_and_push.sh
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

REPO_URI="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/volttron-ven"
eval "$LOGIN_CMD" | docker login --username AWS --password-stdin "$REPO_URI"

cd "$(dirname "$0")"

echo "Building and pushing to $REPO_URI..."
docker build -t volttron-ven .
docker tag volttron-ven:latest "$REPO_URI:latest"
docker push "$REPO_URI:latest"

