
#!/usr/bin/env bash
set -e

PROFILE="${AWS_PROFILE:-}"

if [[ -z "$PROFILE" ]]; then
  echo "Please set AWS_PROFILE to your SSO profile name." >&2
  exit 1
fi

if ! grep -q "\[$PROFILE\]" ~/.aws/config 2>/dev/null; then
  echo "SSO profile $PROFILE not found. Starting aws configure sso..."
  aws configure sso
fi

aws sso login --profile $PROFILE
export AWS_PROFILE=$PROFILE
