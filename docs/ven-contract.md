# VEN ↔ Backend Contract (MQTT + Shadow)

This document defines the MQTT command/ack envelopes, telemetry payloads, and IoT
Thing Shadow schema that the Backend uses to control and observe a VEN.

## Identifiers and Versioning

- `venId`: the AWS IoT Thing Name (also exported as env `IOT_THING_NAME`).
- `schemaVersion`: string, currently `"1.0"`. Included in telemetry and shadow.

## Topics

- Commands to VEN (Backend → VEN): `ven/cmd/{venId}`
- Acks from VEN (VEN → Backend): `ven/ack/{venId}`
- Metering telemetry (VEN → Backend): `oadr/meter/{venId}` (existing)
- Optional detailed loads snapshot (VEN → Backend): `ven/loads/{venId}` (set
  `BACKEND_LOADS_TOPIC` or it defaults to `ven/loads/{thing}`)

## Command Envelope

Backend publishes JSON to `ven/cmd/{venId}`:

```json
{
  "op": "set|setConfig|setLoad|shedLoad|shedPanel|get|event|ping",
  "correlationId": "uuid-or-any",
  "venId": "ven-123",
  "data": { /* op-specific */ }
}
```

Ack from VEN on `ven/ack/{venId}`:

```json
{
  "op": "...",
  "correlationId": "...",
  "ok": true,
  "ts": 1700000000,
  "venId": "ven-123",
  "data": { /* result */ }
}
```

### Supported Ops

- `set` / `setConfig`
  - Data: any of `report_interval_seconds`, `target_power_kw`, power knobs.
  - Ack: `{ applied: { ... } }`

- `setLoad`
  - Data: `{ loadId, enabled?, capacityKw?, priority? }`
  - Ack: `{ updated: { id, name, type, enabled, rated_kw } }`

- `shedLoad`
  - Data: `{ loadId, reduceKw, durationS, eventId? }`
  - Applies a temporary power limit to the load for `durationS`.
  - Ack: `{ limitKw, until }`

- `shedPanel`
  - Data: `{ requestedReductionKw, durationS, eventId? }`
  - VEN applies temporary per-load limits and a temporary panel target.
  - Ack: `{ targetKw, acceptedReduceKw, until }`

- `event`
  - Data: `{ event_id?, start_ts?, end_ts?/duration_s?, requestedReductionKw? }`
  - Starts/marks an event lifecycle and enables M&V during the window.
  - Ack: `{ event_id }`

- `get`
  - Data: `{ what: "status"|"config"|"loads" }`
  - Ack: `{ status }` or `{ config }` or `{ loads }`

- `ping` → Ack: `{ pong: true, ts }`

## Telemetry Payload (oadr/meter/{venId})

Emitted every report interval.

```json
{
  "schemaVersion": "1.0",
  "venId": "ven-123",
  "timestamp": 1700000000,
  "usedPowerKw": 2.73,
  "shedPowerKw": 0.62,
  "requestedReductionKw": 1.0,
  "eventId": "evt-9",
  "batterySoc": 0.54,
  "loads": [ {"id": "hvac1", "currentPowerKw": 0.82 }, ... ],
  
  // Back-compat legacy keys:
  "power_kw": 2.73
}
```

Notes:
- `usedPowerKw` = net grid import (positive). PV generation appears as a negative
  per-load `currentPowerKw` for the PV circuit in the `loads` array.
- `shedPowerKw` is present when an event is active and baseline is computed.

## Optional Loads Snapshot (ven/loads/{venId})

Published occasionally (every `LOADS_PUBLISH_EVERY` intervals; default 6).

```json
{
  "schemaVersion": "1.0",
  "venId": "ven-123",
  "timestamp": 1700000000,
  "loads": [
    {
      "id": "hvac1",
      "name": "HVAC",
      "type": "hvac",
      "capacityKw": 3.5,
      "currentPowerKw": 0.8,
      "shedCapabilityKw": 0.5,
      "enabled": true,
      "priority": 1
    }
  ]
}
```

## IoT Shadow Schema

`state.reported` contains a backend-aligned snapshot:

```json
{
  "schemaVersion": "1.0",
  "ven": { "venId": "ven-123", "enabled": true, "status": "connected", "lastPublishTs": 1700000000 },
  "loads": [ { "id": "hvac1", "type": "hvac", "name": "HVAC", "capacityKw": 3.5, "currentPowerKw": 0.8, "shedCapabilityKw": 0.5, "enabled": true, "priority": 1 } ],
  "metrics": { "currentPowerKw": 2.73, "shedAvailabilityKw": 1.3, "batterySoc": 0.54, "activeEventId": "evt-9", "lastEventSummary": { "eventId": "evt-9", "requestedReductionKw": 1.0, "actualReductionKw": 0.6, "deliveredKwh": 0.25, "baselineKw": 3.35, "startTs": 1700000000, "endTs": 1700001800 } },
  "report_interval_seconds": 30
}
```

`state.desired` accepts updates for config/knobs and load fields (enabled, capacityKw, priority).

## Ambiguities and Decisions

- `currentPowerKw` for PV is negative (generation). Backend may separate generation in its models.
- Baseline is a simple average of up to 5 samples prior to event start (v1). Later versions can adopt more robust methods.
- `shedCapabilityKw` is an instantaneous estimate based on type-specific floors and storage discharge headroom.

## Security Considerations

If exposing `/ui` and `/config` publicly, add an env-gated token and TLS-only access. MQTT commands should be IAM/SigV4-authenticated via the Backend.

