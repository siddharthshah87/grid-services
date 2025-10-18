#!/bin/bash
set -e

echo "🚀 Starting Local VEN"
echo ""

# Get IoT endpoint
IOT_ENDPOINT=$(aws iot describe-endpoint --endpoint-type iot:Data-ATS --query 'endpointAddress' --output text)
echo "Endpoint: $IOT_ENDPOINT"

# Setup certificates (if not already done)
if [ ! -f ./certs/ca.pem ]; then
    echo "📜 Fetching certificates..."
    mkdir -p ./certs
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
    
    echo "✅ Certificates downloaded"
fi

# Set environment variables
export IOT_ENDPOINT="$IOT_ENDPOINT"
export CLIENT_ID="volttron_local_$(date +%s)"
export TELEMETRY_TOPIC="ven/telemetry/$CLIENT_ID"
export CMD_TOPIC="ven/cmd/$CLIENT_ID"
export ACK_TOPIC="ven/ack/$CLIENT_ID"
export CA_CERT="./certs/ca.pem"
export CLIENT_CERT="./certs/client.crt"
export PRIVATE_KEY="./certs/client.key"

echo ""
echo "Configuration:"
echo "  Client ID: $CLIENT_ID"
echo "  Telemetry: $TELEMETRY_TOPIC"
echo "  Commands: $CMD_TOPIC"
echo "  Acks: $ACK_TOPIC"
echo ""

# Run the local VEN
python3 ven_local.py
