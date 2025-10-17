#!/bin/bash
set -e

echo "🚀 Setting up local VEN development environment..."

# Create certs directory if it doesn't exist
mkdir -p ./certs

# Fetch certificates from AWS Secrets Manager
echo "📜 Fetching TLS certificates from AWS Secrets Manager..."
aws secretsmanager get-secret-value \
  --secret-id dev-volttron-tls \
  --query 'SecretString' \
  --output text | jq -r '.ca_cert' > ./certs/ca.pem

aws secretsmanager get-secret-value \
  --secret-id dev-volttron-tls \
  --query 'SecretString' \
  --output text | jq -r '.client_cert' > ./certs/client.crt

aws secretsmanager get-secret-value \
  --secret-id dev-volttron-tls \
  --query 'SecretString' \
  --output text | jq -r '.private_key' > ./certs/client.key

echo "✅ Certificates downloaded to ./certs/"

# Get IoT endpoint
IOT_ENDPOINT=$(aws iot describe-endpoint --endpoint-type iot:Data-ATS --query 'endpointAddress' --output text)
echo "🌐 IoT Endpoint: $IOT_ENDPOINT"

# Set environment variables
# Don't set LOCAL_DEV=1 - we want real TLS with our certificates
export IOT_ENDPOINT="$IOT_ENDPOINT"
export MQTT_CONNECT_HOST="$IOT_ENDPOINT"
export MQTT_TLS_SERVER_NAME="$IOT_ENDPOINT"
export MQTT_PORT=8883
export IOT_THING_NAME="volttron_thing"
export AWS_REGION="us-west-2"
export HEALTH_PORT=8000
export VEN_ID="volttron_thing"
export BACKEND_CMD_TOPIC="ven/cmd/volttron_thing"
export BACKEND_ACK_TOPIC="ven/ack/volttron_thing"
export BACKEND_TELEMETRY_TOPIC="ven/telemetry/volttron_thing"

# Disable TLS secret name so it uses env vars instead
export TLS_SECRET_NAME=""

# Set certificate paths (absolute paths)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export CA_CERT="$SCRIPT_DIR/certs/ca.pem"
export CLIENT_CERT="$SCRIPT_DIR/certs/client.crt"
export PRIVATE_KEY="$SCRIPT_DIR/certs/client.key"

# Install dependencies if needed
if ! python3 -c "import paho.mqtt" 2>/dev/null; then
  echo "📦 Installing Python dependencies..."
  pip install -q -r requirements.txt
fi

echo ""
echo "🎯 Starting local VEN with:"
echo "  - Thing Name: $IOT_THING_NAME"
echo "  - Endpoint: $IOT_ENDPOINT"
echo "  - Command Topic: $BACKEND_CMD_TOPIC"
echo "  - Ack Topic: $BACKEND_ACK_TOPIC"
echo "  - Health Port: $HEALTH_PORT"
echo ""
echo "Press Ctrl+C to stop"
echo "===================="
echo ""

# Run the VEN
python3 ven_agent.py
