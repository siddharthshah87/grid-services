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

# Derive an immutable image tag from the current git commit.
GIT_SHA=$(git rev-parse --short HEAD)
BUILD_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ)

LOCAL_IMAGE="volttron-ven"
TAG_SHA="$REPO_URI:$GIT_SHA"
TAG_LATEST="$REPO_URI:latest"

echo "Building image with tags: $TAG_SHA and latest..."
docker build \
  --build-arg GIT_SHA="$GIT_SHA" \
  --build-arg BUILD_DATE="$BUILD_DATE" \
  -t "$LOCAL_IMAGE:latest" \
  -t "$LOCAL_IMAGE:$GIT_SHA" \
  .

docker tag "$LOCAL_IMAGE:$GIT_SHA" "$TAG_SHA"
docker tag "$LOCAL_IMAGE:latest" "$TAG_LATEST"

echo "Pushing $TAG_SHA"
docker push "$TAG_SHA"
echo "Pushing $TAG_LATEST"
docker push "$TAG_LATEST"

echo "✅ Pushed images:"
echo " - $TAG_SHA"
echo " - $TAG_LATEST"
echo "You can update your task definition to use: $TAG_SHA"
