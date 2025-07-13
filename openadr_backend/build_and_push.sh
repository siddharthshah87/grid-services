
#!/usr/bin/env bash
set -euo pipefail

# Usage: AWS_PROFILE=my-profile ./build_and_push.sh
PROFILE="${AWS_PROFILE:-AdministratorAccess-923675928909}"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text --profile "$PROFILE")
REGION="${AWS_REGION:-us-west-2}"
REPO_URI="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/openadr-backend"

echo "🔐 Logging into ECR for profile $PROFILE..."
aws ecr get-login-password --region "$REGION" --profile "$PROFILE" | \
  docker login --username AWS --password-stdin "$REPO_URI"

echo "🐳 Building Docker image..."
docker build -t openadr-backend .

echo "🏷️ Tagging and pushing to $REPO_URI..."
docker tag openadr-backend:latest "$REPO_URI:latest"
docker push "$REPO_URI:latest"

echo "✅ Done. Image pushed to $REPO_URI:latest"

