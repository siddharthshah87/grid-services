#!/usr/bin/env bash
set -euo pipefail

# 1) Add HashiCorp GPG key ---------------------------------------------------
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://apt.releases.hashicorp.com/gpg | \
  sudo tee /etc/apt/keyrings/hashicorp.asc >/dev/null
sudo chmod 0644 /etc/apt/keyrings/hashicorp.asc

# 2) Add the HashiCorp repo --------------------------------------------------
echo \
  "deb [signed-by=/etc/apt/keyrings/hashicorp.asc] \
  https://apt.releases.hashicorp.com $(lsb_release -cs) main" | \
  sudo tee /etc/apt/sources.list.d/hashicorp.list

# 3) Install Terraform -------------------------------------------------------
sudo apt update -y
sudo apt install -y terraform

# 4) Verify ------------------------------------------------------------------
terraform -version

