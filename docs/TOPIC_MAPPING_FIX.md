# Topic Mapping Analysis & Fix Plan

## Current State (BROKEN ❌)

### VEN Publishes To:
1. `ven/telemetry/{venId}` - Legacy topic (not consumed by backend)
2. `oadr/meter/{venId}` - NEW topic (but backend not listening!)

### Backend Listens To:
1. `volttron/metering` - Via IoT Rule → MQTT Consumer
2. `volttron/dev` - Status topic (legacy)
3. `openadr/event` - Event topic
4. `openadr/response` - Response topic

### IoT Rules:
1. `volttron/metering` → Forwards to backend MQTT endpoint
2. `openadr/event` → Forwards to backend MQTT endpoint

## Problem:
VEN publishes to `oadr/meter/{venId}` but:
- Backend expects `volttron/metering`
- No IoT rule forwards `oadr/meter/#` to backend
- Telemetry is NOT reaching the database!

## Solution Options:

### Option 1: Fix VEN to Use Correct Topic (RECOMMENDED)
Change VEN to publish to `volttron/metering` instead of `oadr/meter/{venId}`

**Pros:**
- Matches existing infrastructure
- No Terraform changes needed
- Works immediately

**Cons:**
- Loses per-VEN topic routing

### Option 2: Add IoT Rule for oadr/meter/#
Create new IoT rule to forward `oadr/meter/#` → backend

**Pros:**
- More flexible topic structure
- Better multi-VEN support

**Cons:**
- Requires Terraform changes
- Need to redeploy infrastructure

### Option 3: Publish to BOTH Topics (QUICK FIX)
VEN publishes to both `volttron/metering` AND `oadr/meter/{venId}`

**Pros:**
- Works immediately
- Backward compatible
- Can migrate gradually

**Cons:**
- Duplicates messages
- Technical debt

## Recommended Fix: Option 1

Change `METERING_TOPIC` in VEN to match backend expectation:

```python
# volttron-ven/ven_local_enhanced.py
# OLD:
METERING_TOPIC = os.getenv("METERING_TOPIC", f"oadr/meter/{CLIENT_ID}")

# NEW:
METERING_TOPIC = os.getenv("METERING_TOPIC", "volttron/metering")
```

## Additional Fixes Needed:

### 1. VEN ID Registration
VEN generates new ID each time: `volttron_local_<timestamp>`
Backend registers VEN with `registrationId`

**Fix**: Use consistent VEN ID, not timestamp-based

### 2. Shadow Topics
Current shadow topics use CLIENT_ID which changes each run

**Fix**: Use IOT_THING_NAME for shadow (consistent identity)

### 3. Command Topic
Backend sends commands to `ven/cmd/{venId}` 
VEN subscribes to `ven/cmd/{CLIENT_ID}`

**Issue**: venId in backend != CLIENT_ID in VEN

**Fix**: Ensure registration_id matches CLIENT_ID

## Complete Fix Implementation:

```python
# volttron-ven/ven_local_enhanced.py

# Use IOT_THING_NAME if provided, otherwise generate once and persist
if os.getenv("IOT_THING_NAME"):
    CLIENT_ID = os.getenv("IOT_THING_NAME")
else:
    # Load from file or create new
    VEN_ID_FILE = os.path.expanduser("~/.volttron_ven_id")
    if os.path.exists(VEN_ID_FILE):
        with open(VEN_ID_FILE, 'r') as f:
            CLIENT_ID = f.read().strip()
    else:
        CLIENT_ID = f"volttron_local_{int(time.time())}"
        with open(VEN_ID_FILE, 'w') as f:
            f.write(CLIENT_ID)

# Topics using consistent ID
TELEMETRY_TOPIC = "volttron/metering"  # Backend topic
CMD_TOPIC = f"ven/cmd/{CLIENT_ID}"
ACK_TOPIC = f"ven/ack/{CLIENT_ID}"

# Shadow topics
SHADOW_UPDATE_TOPIC = f"$aws/things/{CLIENT_ID}/shadow/update"
SHADOW_GET_TOPIC = f"$aws/things/{CLIENT_ID}/shadow/get"
SHADOW_DELTA_TOPIC = f"$aws/things/{CLIENT_ID}/shadow/update/delta"
```

## Testing Plan:

1. Fix METERING_TOPIC to use `volttron/metering`
2. Use consistent VEN ID (from env or file)
3. Register VEN with same ID in backend
4. Start VEN - verify telemetry reaches backend
5. Create event - verify command reaches VEN
6. Verify ACK sent back
7. Verify shadow updates
8. Verify load shedding during event
9. Verify loads restore after event
