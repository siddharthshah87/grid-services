#!/bin/bash
# Simple test runner for minimal VEN

cd "$(dirname "$0")"

# Kill any running VEN
pkill -9 -f "ven_minimal" 2>/dev/null || true
sleep 1

# Export required env vars
IOT_ENDPOINT=$(aws iot describe-endpoint --endpoint-type iot:Data-ATS --query 'endpointAddress' --output text)
export IOT_ENDPOINT
export CLIENT_ID="volttron_minimal_test"
export CA_CERT="./certs/ca.pem"
export CLIENT_CERT="./certs/client.crt"
export PRIVATE_KEY="./certs/client.key"
export TELEMETRY_TOPIC="ven/telemetry/$CLIENT_ID"
export CMD_TOPIC="ven/cmd/$CLIENT_ID"
export ACK_TOPIC="ven/ack/$CLIENT_ID"

echo "=== Running Minimal VEN ==="
echo "Client ID: $CLIENT_ID"
echo "Endpoint: $IOT_ENDPOINT"
echo ""

# Run and capture all output
python3 ven_minimal.py 2>&1 | grep -v "DeprecationWarning" &
VEN_PID=$!
echo "VEN started (PID: $VEN_PID)"

# Wait and check if it's still running
for i in {1..5}; do
    sleep 5
    if ps -p $VEN_PID > /dev/null 2>&1; then
        echo "[$((i*5))s] VEN still running ✓"
    else
        echo "[$((i*5))s] VEN stopped!"
        break
    fi
done

# Stop it
kill $VEN_PID 2>/dev/null || true

echo ""
echo "=== Test Complete ==="
