#!/bin/bash
# Test script for local VEN command reception

set -e

echo "=== Local VEN Command Testing ==="
echo ""

# Kill any existing VEN
pkill -9 -f "python.*ven_agent" 2>/dev/null || true
sleep 2

# Start VEN in background
LOG_FILE="/tmp/ven_test_$(date +%s).log"
echo "📝 Starting VEN (logs: $LOG_FILE)"
cd /workspaces/grid-services/volttron-ven
nohup ./run_local.sh > "$LOG_FILE" 2>&1 &
VEN_PID=$!
echo "✅ VEN started (PID: $VEN_PID)"
echo ""

# Wait for initialization
echo "⏳ Waiting 15 seconds for VEN to initialize..."
sleep 15

# Check if VEN is still running
if ! ps -p $VEN_PID > /dev/null 2>&1; then
    echo "❌ VEN process died! Last logs:"
    tail -20 "$LOG_FILE"
    exit 1
fi

# Show initialization status
echo ""
echo "=== VEN Status ==="
grep -E "Starting local VEN|MQTT.*established|Subscribed to backend|_ven_enable.*completed" "$LOG_FILE" | tail -10 || echo "No status logs found"
echo ""

# Send ping command
CORR_ID="test-local-$(date +%s)"
echo "📤 Sending ping command (correlation ID: $CORR_ID)"
cd /workspaces/grid-services

# Get IoT endpoint
IOT_ENDPOINT=$(aws iot describe-endpoint --endpoint-type iot:Data-ATS --query 'endpointAddress' --output text)
export IOT_ENDPOINT

python3 scripts/ven_cmd_publish.py \
  --op ping \
  --ven-id volttron_thing_local \
  --corr-id "$CORR_ID"

echo ""
echo "⏳ Waiting 5 seconds for VEN to process command..."
sleep 5

# Check for command reception in logs
echo ""
echo "=== Checking for Command Reception ==="
if grep -i "backend command.*$CORR_ID\|ping.*$CORR_ID" "$LOG_FILE" > /dev/null 2>&1; then
    echo "✅ COMMAND RECEIVED! VEN logs:"
    grep -A5 -B2 -i "backend command\|ping" "$LOG_FILE" | tail -15
else
    echo "❌ No command reception found in logs"
    echo ""
    echo "Recent VEN logs:"
    tail -20 "$LOG_FILE"
fi

echo ""
echo "=== Full log file: $LOG_FILE ==="
echo "View with: tail -f $LOG_FILE"
echo ""
echo "VEN is still running (PID: $VEN_PID)"
echo "Kill with: kill $VEN_PID"
