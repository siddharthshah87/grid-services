#!/bin/bash
# VEN Control Script - Unified interface for VEN operations

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VEN_DIR="$PROJECT_ROOT/volttron-ven"

# Default values
VEN_ID="volttron_thing"
BACKEND_URL="http://backend-alb-948465488.us-west-2.elb.amazonaws.com"
IOT_ENDPOINT="${IOT_ENDPOINT:-$(aws iot describe-endpoint --endpoint-type iot:Data-ATS --query 'endpointAddress' --output text 2>/dev/null || echo 'a1mgxpe8mg484j-ats.iot.us-west-2.amazonaws.com')}"

show_usage() {
    cat << EOF
🎛️  VEN Control Script

Usage: $0 <command> [options]

Commands:
  start             Start the VEN in background
  stop              Stop the running VEN
  restart           Restart the VEN
  status            Check VEN status
  logs              Show VEN logs (tail -f)
  send-event        Send a DR event command to VEN
  restore           Send restore command to VEN
  register          Register VEN in backend database
  shadow            Get VEN shadow from AWS IoT
  telemetry         Monitor VEN telemetry topic

Options:
  --ven-id <id>     VEN ID (default: volttron_thing)
  --shed-kw <kw>    kW to shed for DR event
  --duration <sec>  Duration in seconds for DR event
  --event-id <id>   Event ID

Examples:
  # Start VEN
  $0 start

  # Send DR event (shed 2 kW for 5 minutes)
  $0 send-event --shed-kw 2.0 --duration 300

  # Check status
  $0 status

  # View logs
  $0 logs

Environment Variables:
  BACKEND_URL       Backend API URL
  IOT_ENDPOINT      AWS IoT endpoint
  AWS_REGION        AWS region (default: us-west-2)

EOF
}

check_dependencies() {
    local missing=()
    command -v aws >/dev/null 2>&1 || missing+=("aws-cli")
    command -v python3 >/dev/null 2>&1 || missing+=("python3")
    command -v jq >/dev/null 2>&1 || missing+=("jq")
    
    if [ ${#missing[@]} -ne 0 ]; then
        echo "❌ Missing dependencies: ${missing[*]}"
        echo "   Install with: apt-get install ${missing[*]}"
        exit 1
    fi
}

start_ven() {
    echo "🚀 Starting VEN..."
    cd "$VEN_DIR"
    
    if pgrep -f "python3.*ven_local_enhanced" > /dev/null; then
        echo "⚠️  VEN is already running"
        return
    fi
    
    ./run_enhanced.sh --background
    sleep 2
    
    if pgrep -f "python3.*ven_local_enhanced" > /dev/null; then
        echo "✅ VEN started successfully"
        echo "   Web UI: http://localhost:8080"
    else
        echo "❌ Failed to start VEN"
        exit 1
    fi
}

stop_ven() {
    echo "🛑 Stopping VEN..."
    if pkill -f "python3.*ven_local_enhanced"; then
        echo "✅ VEN stopped"
    else
        echo "⚠️  No VEN process found"
    fi
}

restart_ven() {
    stop_ven
    sleep 2
    start_ven
}

show_status() {
    echo "📊 VEN Status"
    echo ""
    
    # Check process
    if pgrep -f "python3.*ven_local_enhanced" > /dev/null; then
        PID=$(pgrep -f "python3.*ven_local_enhanced")
        echo "✅ Process: Running (PID: $PID)"
    else
        echo "❌ Process: Not running"
    fi
    
    # Check web UI
    if curl -s http://localhost:8080 > /dev/null 2>&1; then
        echo "✅ Web UI: Accessible at http://localhost:8080"
    else
        echo "❌ Web UI: Not accessible"
    fi
    
    # Check backend registration
    echo ""
    echo "Backend Status:"
    VEN_INFO=$(curl -s "$BACKEND_URL/api/vens/" | jq -r ".[] | select(.id == \"$VEN_ID\") | {status, power: .metrics.currentPowerKw}" 2>/dev/null || echo "null")
    if [ "$VEN_INFO" != "null" ]; then
        echo "$VEN_INFO" | jq '.'
    else
        echo "⚠️  VEN not found in backend database"
    fi
}

show_logs() {
    if [ -f /tmp/ven_enhanced.log ]; then
        tail -f /tmp/ven_enhanced.log
    else
        echo "❌ Log file not found: /tmp/ven_enhanced.log"
        echo "   VEN may not be running in background mode"
    fi
}

send_event() {
    local SHED_KW="$1"
    local DURATION="$2"
    local EVENT_ID="${3:-evt-manual-$(date +%s)}"
    
    if [ -z "$SHED_KW" ] || [ -z "$DURATION" ]; then
        echo "Usage: $0 send-event --shed-kw <kw> --duration <seconds> [--event-id <id>]"
        exit 1
    fi
    
    echo "📨 Sending DR event command..."
    echo "   VEN ID: $VEN_ID"
    echo "   Shed: $SHED_KW kW"
    echo "   Duration: $DURATION seconds"
    echo "   Event ID: $EVENT_ID"
    
    python3 "$SCRIPT_DIR/ven_cmd_publish.py" \
        --ven-id "$VEN_ID" \
        --endpoint "$IOT_ENDPOINT" \
        --op event \
        --shed-kw "$SHED_KW" \
        --duration "$DURATION" \
        --event-id "$EVENT_ID"
}

send_restore() {
    echo "🔄 Sending restore command..."
    python3 "$SCRIPT_DIR/ven_cmd_publish.py" \
        --ven-id "$VEN_ID" \
        --endpoint "$IOT_ENDPOINT" \
        --op restore
}

register_ven() {
    echo "📝 Registering VEN in backend..."
    python3 "$SCRIPT_DIR/register_ven.py" \
        --backend-url "${BACKEND_URL#http://}" \
        --ven-id "$VEN_ID" \
        --name "VEN $VEN_ID" \
        --status online
}

get_shadow() {
    echo "🔍 Fetching VEN shadow..."
    aws iot-data get-thing-shadow \
        --thing-name "$VEN_ID" \
        --region "${AWS_REGION:-us-west-2}" \
        /dev/stdout 2>&1 | jq '.state.reported | {power_kw, shed_kw, active_event, circuits: [.circuits[]? | {name, enabled, current_kw}]}'
}

monitor_telemetry() {
    echo "📡 Monitoring telemetry topic: volttron/metering"
    echo "   Press Ctrl+C to stop"
    python3 "$SCRIPT_DIR/ven_telemetry_listen.py"
}

# Parse command
COMMAND="${1:-}"
shift || true

# Parse options
SHED_KW=""
DURATION=""
EVENT_ID=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --ven-id)
            VEN_ID="$2"
            shift 2
            ;;
        --shed-kw)
            SHED_KW="$2"
            shift 2
            ;;
        --duration)
            DURATION="$2"
            shift 2
            ;;
        --event-id)
            EVENT_ID="$2"
            shift 2
            ;;
        --help|-h)
            show_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Execute command
case "$COMMAND" in
    start)
        check_dependencies
        start_ven
        ;;
    stop)
        stop_ven
        ;;
    restart)
        check_dependencies
        restart_ven
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    send-event)
        send_event "$SHED_KW" "$DURATION" "$EVENT_ID"
        ;;
    restore)
        send_restore
        ;;
    register)
        register_ven
        ;;
    shadow)
        get_shadow
        ;;
    telemetry)
        monitor_telemetry
        ;;
    ""|-h|--help)
        show_usage
        exit 0
        ;;
    *)
        echo "Unknown command: $COMMAND"
        show_usage
        exit 1
        ;;
esac
