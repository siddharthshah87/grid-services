#!/bin/bash
# Quick VEN End-to-End Test Script

set -e

BACKEND_URL="http://backend-alb-948465488.us-west-2.elb.amazonaws.com"
VEN_ID="test-ven-quick-$(date +%s)"

echo "=========================================="
echo "Quick VEN End-to-End Test"
echo "=========================================="
echo ""

# Test 1: Backend Health
echo "1️⃣ Testing Backend Health..."
HEALTH=$(curl -s "${BACKEND_URL}/health")
if echo "$HEALTH" | grep -q "ok"; then
    echo "   ✅ Backend is healthy"
else
    echo "   ❌ Backend health check failed"
    exit 1
fi

# Test 2: Register VEN
echo ""
echo "2️⃣ Registering VEN: $VEN_ID"
VEN_RESPONSE=$(curl -s -X POST "${BACKEND_URL}/api/vens/" \
    -H "Content-Type: application/json" \
    -d "{
        \"name\": \"Quick Test VEN\",
        \"status\": \"online\",
        \"location\": {\"lat\": 37.7749, \"lon\": -122.4194},
        \"registrationId\": \"${VEN_ID}\"
    }")

VEN_DB_ID=$(echo "$VEN_RESPONSE" | jq -r '.id' 2>/dev/null)
if [ -n "$VEN_DB_ID" ] && [ "$VEN_DB_ID" != "null" ]; then
    echo "   ✅ VEN registered with database ID: $VEN_DB_ID"
else
    echo "   ❌ Failed to register VEN"
    echo "   Response: $VEN_RESPONSE"
    exit 1
fi

# Test 3: Create Event
echo ""
echo "3️⃣ Creating DR Event..."
START_TIME=$(date -u -d '+30 seconds' +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -v+30S +%Y-%m-%dT%H:%M:%SZ)
END_TIME=$(date -u -d '+2 minutes' +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -v+2M +%Y-%m-%dT%H:%M:%SZ)

EVENT_RESPONSE=$(curl -s -X POST "${BACKEND_URL}/api/events/" \
    -H "Content-Type: application/json" \
    -d "{
        \"status\": \"scheduled\",
        \"startTime\": \"${START_TIME}\",
        \"endTime\": \"${END_TIME}\",
        \"requestedReductionKw\": 2.0
    }")

EVENT_ID=$(echo "$EVENT_RESPONSE" | jq -r '.id' 2>/dev/null)
if [ -n "$EVENT_ID" ] && [ "$EVENT_ID" != "null" ]; then
    echo "   ✅ Event created: $EVENT_ID"
    echo "   📅 Starts at: $START_TIME (in ~30 seconds)"
    echo "   ⚡ Reduction: 2.0 kW"
else
    echo "   ❌ Failed to create event"
    echo "   Response: $EVENT_RESPONSE"
    exit 1
fi

# Test 4: Instructions for manual VEN test
echo ""
echo "=========================================="
echo "Next Steps: Start VEN and Monitor"
echo "=========================================="
echo ""
echo "4️⃣ In a new terminal, start the VEN:"
echo ""
echo "   cd volttron-ven"
echo "   export CLIENT_ID=$VEN_ID"
echo "   export IOT_THING_NAME=$VEN_ID"
echo "   ./run_enhanced.sh"
echo ""
echo "5️⃣ Watch for these indicators:"
echo "   - VEN connects to AWS IoT Core"
echo "   - In ~30 seconds, VEN should receive DR EVENT command"
echo "   - Load circuits should show reduced power"
echo "   - Event banner appears in Web UI: http://localhost:8080"
echo ""
echo "6️⃣ Monitor event metrics:"
echo ""
echo "   curl -s ${BACKEND_URL}/api/events/${EVENT_ID}/metrics | jq ."
echo ""
echo "=========================================="
echo "✅ Test setup complete!"
echo "=========================================="
