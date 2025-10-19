#!/bin/bash
set -e

# Ensure we run from the script directory so relative paths (./certs, ven_local_enhanced.py) resolve
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Parse command line arguments
BACKGROUND=false
while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--background)
            BACKGROUND=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [-b|--background]"
            exit 1
            ;;
    esac
done

echo "🚀 Starting Enhanced Local VEN"
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

# CRITICAL: Use IOT_THING_NAME for consistent identity
# The certificates are associated with "volttron_thing" in AWS IoT Core
export IOT_THING_NAME="volttron_thing"
export IOT_ENDPOINT="$IOT_ENDPOINT"

# Backend URL for registration and web UI
export BACKEND_URL="${BACKEND_URL:-http://backend-alb-948465488.us-west-2.elb.amazonaws.com}"

# Certificate paths
export CA_CERT="./certs/ca.pem"
export CLIENT_CERT="./certs/client.crt"
export PRIVATE_KEY="./certs/client.key"
export WEB_PORT="8080"

echo ""
echo "Configuration:"
echo "  Thing Name: $IOT_THING_NAME (consistent identity)"
echo "  IoT Endpoint: $IOT_ENDPOINT"
echo "  Backend: $BACKEND_URL"
echo "  Command Topic: ven/cmd/$IOT_THING_NAME"
echo "  Web UI: http://localhost:$WEB_PORT"
echo ""

# Install Flask if needed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "📦 Installing Flask..."
    pip install flask==3.0.0 --quiet
fi

# Run the enhanced VEN
if [ "$BACKGROUND" = true ]; then
    echo "Starting VEN in background..."
    nohup python3 ven_local_enhanced.py > /tmp/ven_enhanced.log 2>&1 &
    VEN_PID=$!
    echo "✅ VEN started with PID $VEN_PID"
    echo "   Logs: tail -f /tmp/ven_enhanced.log"
    echo "   Stop: kill $VEN_PID"
    sleep 3
    if ps -p $VEN_PID > /dev/null; then
        echo "✅ VEN is running"
    else
        echo "❌ VEN failed to start. Check /tmp/ven_enhanced.log"
        exit 1
    fi
else
    python3 ven_local_enhanced.py
fi
