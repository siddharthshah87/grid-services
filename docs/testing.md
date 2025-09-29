# Testing the VEN Control Plane and Telemetry

This guide shows how to exercise the new VEN control plane (commands over MQTT)
and observe state via the Thing Shadow and the VEN’s /live HTTP endpoint.

## Prerequisites

- AWS credentials available in your shell (AWS SSO or aws-vault).
- The development environment deployed with Terraform (VEN service running).
- Python 3 with the following packages:
  - `boto3` for publishing commands and reading the Thing Shadow
  - `requests` for polling the VEN’s `/live` endpoint
  - `awscrt` and `awsiotsdk` for listening to MQTT acks over WebSockets

Install dependencies:

```
pip install boto3 requests awscrt awsiotsdk
```

Gather outputs (from `envs/dev`):

```
THING_NAME=$(terraform output -raw thing_name)
IOT_ENDPOINT=$(terraform output -raw iot_endpoint)
VEN_URL=https://sim.gridcircuit.link
```

Export environment variables if you prefer not to pass flags:

```
export AWS_REGION=us-west-2
export IOT_ENDPOINT=$IOT_ENDPOINT
```

## Scripts Overview

- `scripts/ven_cmd_publish.py` – publishes backend-style commands to the VEN via AWS IoT Data.
- `scripts/ven_acks_listen.py` – subscribes to `ven/ack/{venId}` via IoT Core WebSockets and prints acks.
- `scripts/ven_shadow_get.py` – reads the Thing Shadow (`state.reported`) for the VEN.
- `scripts/ven_http_live.py` – polls the VEN’s `/live` endpoint and prints a compact JSON summary.

The UI at the VEN URL also shows a “Virtual Panel” with live power, event
banners and circuit cards for quick manual control:

```
$VEN_URL
```

## Listen for Acks (optional but recommended)

```
./scripts/ven_acks_listen.py \
  --ven-id "$THING_NAME" \
  --endpoint "$IOT_ENDPOINT"
```

Filter by correlation ID:

```
./scripts/ven_acks_listen.py --ven-id "$THING_NAME" --endpoint "$IOT_ENDPOINT" --filter-corr corr-123
```

## Publish Commands

Use `ven_cmd_publish.py` with an operation (`--op`) and optional JSON `--data`.
Supported ops: `set|setConfig|setLoad|shedLoad|shedPanel|get|event|ping`.

- Set runtime config (report interval and target power):

```
./scripts/ven_cmd_publish.py \
  --ven-id "$THING_NAME" \
  --endpoint "$IOT_ENDPOINT" \
  --op setConfig \
  --data '{"report_interval_seconds": 15, "target_power_kw": 1.3}' \
  --corr-id cfg-1
```

- Update a load (enable HVAC and set capacity):

```
./scripts/ven_cmd_publish.py \
  --ven-id "$THING_NAME" \
  --endpoint "$IOT_ENDPOINT" \
  --op setLoad \
  --data '{"loadId": "hvac1", "enabled": true, "capacityKw": 3.5, "priority": 1}' \
  --corr-id load-1
```

- Shed a specific load (limit EV by 2 kW for 15 minutes):

```
./scripts/ven_cmd_publish.py \
  --ven-id "$THING_NAME" \
  --endpoint "$IOT_ENDPOINT" \
  --op shedLoad \
  --data '{"loadId": "ev1", "reduceKw": 2.0, "durationS": 900, "eventId": "evt-9"}' \
  --corr-id shed-ev
```

- Panel-level shed (reduce panel by 1.5 kW for 10 minutes):

```
./scripts/ven_cmd_publish.py \
  --ven-id "$THING_NAME" \
  --endpoint "$IOT_ENDPOINT" \
  --op shedPanel \
  --data '{"requestedReductionKw": 1.5, "durationS": 600, "eventId": "evt-10"}' \
  --corr-id shed-panel
```

- Start an event window (10 minutes, 1.0 kW requested reduction):

```
NOW=$(date +%s)
./scripts/ven_cmd_publish.py \
  --ven-id "$THING_NAME" \
  --endpoint "$IOT_ENDPOINT" \
  --op event \
  --data '{"event_id": "evt-200", "start_ts": '$NOW', "duration_s": 600, "requestedReductionKw": 1.0}' \
  --corr-id ev-200
```

- Ping / Get status/config/loads:

```
./scripts/ven_cmd_publish.py --ven-id "$THING_NAME" --endpoint "$IOT_ENDPOINT" --op ping
./scripts/ven_cmd_publish.py --ven-id "$THING_NAME" --endpoint "$IOT_ENDPOINT" --op get --data '{"what":"status"}'
```

## Observe Live State

- Poll the VEN `/live` endpoint:

```
./scripts/ven_http_live.py --base-url "$VEN_URL" --interval 2
```

Sample output:

```
{"ok": true, "power_kw": 2.3, "shed_kw": 0.7, "event_status": "active", "event": "evt-200"}
```

- Open the Virtual Panel in a browser and watch the event banner:

```
$VEN_URL
```

## Inspect the Thing Shadow

```
./scripts/ven_shadow_get.py --ven-id "$THING_NAME" --endpoint "$IOT_ENDPOINT"
```

This prints `state.reported`, including `ven`, `loads`, `metrics` and
`schemaVersion`. After an event ends, `metrics.lastEventSummary` shows
`actualReductionKw` and `deliveredKwh`.

## Notes

- `boto3` IoT Data can publish commands and read the Thing Shadow; it cannot
  subscribe. Use the WebSocket listener (`ven_acks_listen.py`) or route acks to
  SQS/Kinesis via an IoT Rule if you prefer queue consumption.
- Ensure you pass the ATS data endpoint (e.g., `a1…-ats.iot.us-west-2.amazonaws.com`).
- All commands support `--corr-id`; acks include the same `correlationId`.
