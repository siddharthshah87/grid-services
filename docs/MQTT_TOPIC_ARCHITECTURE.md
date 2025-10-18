# MQTT Topic Architecture & Scalability

## Executive Summary

**Key Decision: Use a SHARED topic (`volttron/metering`) for ALL VEN telemetry with VEN ID embedded in the payload.**

This is the correct architecture for scalability. Here's why:

## Current Architecture

### Publishing Strategy
```
ALL VENs → "volttron/metering" (SHARED TOPIC)
  Payload includes: { "venId": "ven-001", "timestamp": ..., "power": ... }
```

### Topic Flow
```
VEN (any ID)
  ↓ publishes to "volttron/metering"
AWS IoT Rule "mqtt-forward-volttron_metering"
  ↓ forwards to Kinesis Stream
Backend MQTT Consumer
  ↓ subscribes to "volttron/metering"
Database (INSERT with venId from payload)
```

## Why This Design Scales

### ✅ Advantages

1. **Single IoT Rule**
   - Only ONE rule to manage: `mqtt-forward-volttron_metering`
   - No need to create rules per VEN
   - Cost: Fixed (1 rule regardless of VEN count)

2. **Single Backend Subscription**
   - Backend subscribes to ONE topic: `volttron/metering`
   - No dynamic subscription management needed
   - Connection overhead: O(1) not O(n)

3. **Simple Infrastructure**
   - IoT Rule SQL: `SELECT * FROM 'volttron/metering'`
   - No wildcards, no complex routing
   - Easy to monitor and debug

4. **Database Partitioning**
   - VEN identification happens in APPLICATION layer (payload parsing)
   - Database can partition by venId column
   - Queries filter by venId: `WHERE ven_id = 'ven-001'`

5. **AWS IoT Core Billing**
   - Charged per message, NOT per topic
   - 1000 VENs on 1 topic = same cost as 1000 VENs on 1000 topics
   - Simplicity reduces operational overhead

### ❌ Per-VEN Topics Would Be Bad

If we used `volttron/metering/{venId}`:

1. **Rule Explosion**
   - Need wildcards: `SELECT * FROM 'volttron/metering/#'`
   - Or create 1000s of rules (management nightmare)

2. **Backend Complexity**
   - Subscribe to wildcard: `volttron/metering/#`
   - Parse topic string to extract VEN ID
   - More error-prone

3. **No Performance Benefit**
   - Backend still processes all messages sequentially
   - Database writes are the bottleneck, not topic routing

4. **Harder Monitoring**
   - Can't see "total VEN traffic" easily
   - CloudWatch metrics scattered across topics

## Command Topics (Per-VEN)

Commands SHOULD be per-VEN because:

```
Backend → "ven/cmd/{venId}" → Specific VEN
```

### Why Per-VEN Commands Are Correct

1. **Targeted Delivery**
   - Only the intended VEN receives the command
   - No filtering needed by VEN

2. **Security**
   - IoT policies can restrict: `ven/cmd/ven-001` to thing `ven-001`
   - Prevent VENs from seeing other VENs' commands

3. **Small Volume**
   - Commands are rare (DR events)
   - Telemetry is continuous (every 5-30 seconds)

## Current Implementation

### VEN Code (ven_local_enhanced.py)
```python
# SHARED telemetry topic - ALL VENs use this
METERING_TOPIC = "volttron/metering"

# PER-VEN command topic
COMMAND_TOPIC = f"ven/cmd/{CLIENT_ID}"

# Payload includes VEN identity
payload = {
    "venId": CLIENT_ID,
    "timestamp": time.time(),
    "totalPower": total_power,
    "circuits": [...]
}
mqtt_client.publish(METERING_TOPIC, json.dumps(payload))
```

### Backend Code (config.py)
```python
mqtt_topic_metering: str = "volttron/metering"  # ALL VENs publish here

@property
def mqtt_topics(self) -> list[str]:
    return [
        self.mqtt_topic_metering,  # "volttron/metering"
        # Other topics...
    ]
```

### IoT Rule (main.tf)
```terraform
module "iot_rule_forwarder" {
  topics = ["volttron/metering"]  # Single shared topic
}

# Terraform creates:
# aws_iot_topic_rule.forward_rules["volttron/metering"]
#   sql = "SELECT * FROM 'volttron/metering'"
```

## Scaling Numbers

### At 1,000 VENs

**SHARED Topic Approach:**
- IoT Rules: 1
- Backend Subscriptions: 1
- Messages/minute: 12,000 (1000 VENs × 12 msgs/min)
- Database writes: 12,000/min to `ven_telemetry` table
- CloudWatch metric: Single `volttron/metering` publish count

**Cost:**
- IoT Core: $5/million messages = $0.36/hour for 12k msgs/min
- Kinesis: 1 shard sufficient for 1000 records/sec

### At 10,000 VENs

**SHARED Topic Approach:**
- IoT Rules: Still 1
- Backend Subscriptions: Still 1
- Messages/minute: 120,000
- Kinesis: Need ~3 shards (120k/min = 2k/sec)

**No architectural changes needed!**

## VEN Identity Management

### Critical Requirements

1. **Consistent CLIENT_ID**
   ```python
   # VEN uses IOT_THING_NAME if set (recommended)
   CLIENT_ID = os.getenv("IOT_THING_NAME") or f"volttron_local_{int(time.time())}"
   ```

2. **Register BEFORE Starting**
   ```bash
   # 1. Set consistent ID
   export IOT_THING_NAME=ven-001
   
   # 2. Register VEN (creates DB record)
   curl -X POST backend/api/vens/ -d '{"venId": "ven-001", ...}'
   
   # 3. Start VEN (uses same ID)
   ./run_enhanced.sh
   ```

3. **Database Lookup**
   ```sql
   -- Backend can find telemetry for specific VEN
   SELECT * FROM ven_telemetry 
   WHERE ven_id = 'ven-001' 
   ORDER BY timestamp DESC 
   LIMIT 100;
   ```

## Topic Summary Table

| Topic Pattern | Usage | Scalability | Security |
|--------------|-------|-------------|----------|
| `volttron/metering` | ALL VEN telemetry | ✅ Perfect | ✅ Read-only for all |
| `ven/cmd/{venId}` | Commands to VEN | ✅ Per-VEN needed | ✅ Policy enforced |
| `ven/ack/{venId}` | ACKs from VEN | ✅ Low volume | ✅ Policy enforced |
| `ven/telemetry/{venId}` | Debugging only | ⚠️ Optional | ⚠️ Extra overhead |

## Recommendation

**✅ KEEP current architecture:**
- Shared `volttron/metering` for ALL VENs
- VEN ID in payload
- Per-VEN command topics for security
- No changes needed for scale

**❌ DO NOT create per-VEN telemetry topics**

## Testing Verification

To verify topic routing works:

```bash
# 1. Check IoT Rule exists
aws iot get-topic-rule --rule-name mqtt_forward_volttron_metering

# 2. Verify Kinesis stream
aws kinesis describe-stream --stream-name mqtt-forward-mqtt-stream

# 3. Check backend subscription
curl http://backend-alb-xxx.elb.amazonaws.com/health

# 4. Publish test message
aws iot-data publish \
  --topic "volttron/metering" \
  --payload '{"venId":"test-ven","power":5000}' \
  --region us-west-2

# 5. Check database
psql -h $DB_HOST -U $DB_USER -d $DB_NAME \
  -c "SELECT * FROM ven_telemetry WHERE ven_id='test-ven' ORDER BY timestamp DESC LIMIT 1;"
```

## Conclusion

**Current design is optimal for scaling to thousands of VENs. No changes needed.**

The VEN ID is correctly embedded in the payload, not the topic name. This is standard practice for pub/sub systems with many publishers.
