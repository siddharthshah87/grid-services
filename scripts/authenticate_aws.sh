
#!/usr/bin/env bash
set -e

PROFILE="AdministratorAccess-923675928909"

if ! grep -q "\[$PROFILE\]" ~/.aws/config 2>/dev/null; then
  echo "SSO profile $PROFILE not found. Starting aws configure sso..."
  aws configure sso
fi

aws sso login --profile $PROFILE
export AWS_PROFILE=$PROFILE
