#!/usr/bin/env bash
set -euo pipefail

# Where we’ll stage the PEM files
install -d -m 0700 /tmp/ven

# Iterate over the three env vars that ECS will inject
for var in CA_CERT CLIENT_CERT PRIVATE_KEY; do
  val="${!var:-}"                           # expand the variable by name
  if [[ -n $val && $val == *"-----BEGIN"* ]]; then
    # Variable holds raw PEM → materialise to a file
    dest="/tmp/ven/${var,,}.pem"            # ca_cert.pem, client_cert.pem, …
    printf '%s\n' "$val" > "$dest"
    chmod 0400 "$dest"
    export "$var"="$dest"                   # flip the env var to the file path
  fi
done

exec python /app/ven_agent.py

