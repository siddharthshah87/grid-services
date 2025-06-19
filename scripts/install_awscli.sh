#!/usr/bin/env bash
set -euo pipefail

# Detect CPU architecture (x86_64 or aarch64) -------------------------------
ARCH=$(uname -m)
case "$ARCH" in
  x86_64)   PKG_URL="https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" ;;
  aarch64)  PKG_URL="https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" ;;
  *)        echo "Unsupported architecture: $ARCH"; exit 1 ;;
esac

# 1) Ensure prerequisites ----------------------------------------------------
apt update -y
apt install -y unzip curl

# 2) Download & install ------------------------------------------------------
curl -sSL "$PKG_URL" -o /tmp/awscliv2.zip
unzip -q /tmp/awscliv2.zip -d /tmp
/tmp/aws/install --update               # idempotent: installs or upgrades

# 3) Enable tab-completion ---------------------------------------------------
if ! grep -q 'aws_completer' ~/.bashrc; then
  echo 'complete -C /usr/local/bin/aws_completer aws' >> ~/.bashrc
fi

# 4) Clean up ---------------------------------------------------------------
rm -rf /tmp/aws /tmp/awscliv2.zip

echo
echo "✅ AWS CLI installed:"
aws --version
echo "→ Open a new shell (or run 'source ~/.bashrc') for tab-completion."

