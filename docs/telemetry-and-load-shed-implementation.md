# Telemetry and Load Shedding Implementation

## Overview
This document tracks the implementation of MQTT telemetry consumption, load shedding automation, and historical data analysis for the OpenADR VEN system.

## Current Status (October 13, 2025)

### ✅ Completed
1. **Backend MQTT Consumer** - Fully functional
   - TLS certificate handling from AWS Secrets Manager
   - Auto-registration of VENs on first telemetry
   - Database persistence of telemetry data
   - Lifespan-based startup with proper error handling

2. **Security Configuration**
   - VPC endpoint security group rules added for Secrets Manager access
   - IAM policies configured for IoT Core and Secrets Manager

3. **VOLTTRON VEN Telemetry Publishing** - Code fixed
   - Fixed critical bug where telemetry was constructed but never published
   - Added proper MQTT publish call with QoS=1
   - Added logging for telemetry publishing
   - Shadow state updates integrated

### 🔨 In Progress
1. **Network Connectivity Issue**
   - VOLTTRON VEN cannot connect to AWS IoT Core
   - Error: `[Errno 101] Network is unreachable`
   - **Root Cause**: Likely security group or VPC endpoint configuration
   - **Impact**: Telemetry not flowing until resolved

### 📋 Pending Implementation

#### 1. Event-Driven Load Shedding
**Objective**: VOLTTRON VEN automatically reduces load when OpenADR events are received

**Implementation Plan**:
```python
# In ven_agent.py - enhance on_backend_cmd or on_event
def handle_load_shed_event(event_data):
    """
    Respond to OpenADR event by reducing load
    
    Args:
        event_data: {
            "event_id": str,
            "start_ts": int,
            "end_ts": int,
            "requested_kw": float,  # Target reduction
            "baseline_kw": float     # Pre-event baseline
        }
    """
    # 1. Calculate current baseline from recent history
    baseline = calculate_baseline_power()
    
    # 2. Determine target power level
    target_kw = baseline - event_data["requested_kw"]
    target_kw = max(0, target_kw)  # Can't go negative
    
    # 3. Execute load shedding strategy
    circuits_to_shed = select_circuits_for_shedding(target_kw)
    
    # 4. Update circuit states
    for circuit in circuits_to_shed:
        set_circuit_state(circuit["id"], "off")
    
    # 5. Update shadow with event participation
    update_shadow_event_status(event_data, target_kw)
    
    # 6. Monitor and adjust during event
    schedule_event_monitoring(event_data)
```

**Circuit Selection Strategy**:
- **Priority 1**: Non-essential loads (pool pump, EV charger when not needed)
- **Priority 2**: HVAC setpoint adjustment (increase temp in summer, decrease in winter)
- **Priority 3**: Water heater (use thermal storage capacity)
- **Priority 4**: Battery discharge to offset grid consumption

#### 2. Baseline Power Calculation
**Objective**: Accurate baseline estimation even with limited historical data

**Algorithm Design**:
```python
def calculate_baseline_power(
    historical_data: List[Tuple[int, float]],
    current_time: int,
    lookback_minutes: int = 60
) -> float:
    """
    Calculate baseline power consumption
    
    Strategies (in order of preference):
    1. Same time yesterday (if available)
    2. Average of last N samples before event start
    3. Rolling 24-hour average for same hour
    4. Overall average (fallback for new VENs)
    """
    # Strategy 1: Yesterday at same time
    yesterday_time = current_time - 86400
    yesterday_data = get_data_near_timestamp(historical_data, yesterday_time, window=300)
    if yesterday_data:
        return calculate_average(yesterday_data)
    
    # Strategy 2: Recent pre-event average
    recent_data = get_recent_samples(historical_data, current_time, lookback_minutes)
    if len(recent_data) >= 10:  # Need reasonable sample size
        return calculate_weighted_average(recent_data)  # More weight to recent
    
    # Strategy 3: Rolling 24h average for this hour
    hour_of_day = datetime.fromtimestamp(current_time).hour
    historical_same_hour = filter_by_hour(historical_data, hour_of_day)
    if len(historical_same_hour) >= 5:
        return calculate_average(historical_same_hour)
    
    # Strategy 4: Overall average (fallback)
    if len(historical_data) > 0:
        return calculate_average(historical_data)
    
    # Default: Use current power as baseline estimate
    return get_current_power()


def calculate_weighted_average(data: List[Tuple[int, float]]) -> float:
    """
    Calculate weighted average giving more weight to recent samples
    
    Weight formula: w_i = 1 / (1 + age_hours)
    """
    if not data:
        return 0.0
    
    now = data[-1][0]  # Most recent timestamp
    weighted_sum = 0.0
    weight_total = 0.0
    
    for ts, value in data:
        age_hours = (now - ts) / 3600.0
        weight = 1.0 / (1.0 + age_hours)
        weighted_sum += value * weight
        weight_total += weight
    
    return weighted_sum / weight_total if weight_total > 0 else 0.0
```

#### 3. Load Shed Measurement Service
**Objective**: Post-event analysis of load shedding effectiveness

**Database Schema Extensions**:
```sql
-- Add to VenTelemetry or create new EventPerformance table
CREATE TABLE IF NOT EXISTS event_performance (
    id SERIAL PRIMARY KEY,
    ven_id VARCHAR(255) NOT NULL,
    event_id VARCHAR(255) NOT NULL,
    
    -- Timestamps
    event_start_ts INTEGER NOT NULL,
    event_end_ts INTEGER NOT NULL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Power metrics (in kW)
    baseline_kw FLOAT NOT NULL,          -- Estimated baseline power
    requested_reduction_kw FLOAT NOT NULL, -- Requested shed amount
    target_kw FLOAT NOT NULL,             -- Baseline - requested
    
    -- Actual performance
    avg_actual_kw FLOAT NOT NULL,         -- Actual avg power during event
    achieved_reduction_kw FLOAT NOT NULL, -- Baseline - actual
    
    -- Performance metrics
    shed_percentage FLOAT,                -- (achieved/requested) * 100
    delivered_kwh FLOAT,                  -- Total energy shed
    
    -- Confidence metrics
    baseline_confidence VARCHAR(50),       -- "high", "medium", "low"
    data_points_count INTEGER,            -- Number of telemetry samples
    
    FOREIGN KEY (ven_id) REFERENCES vens(ven_id),
    UNIQUE(ven_id, event_id)
);
```

**Calculation Logic**:
```python
async def calculate_event_performance(
    ven_id: str,
    event_id: str,
    event_start: int,
    event_end: int
) -> EventPerformance:
    """
    Calculate load shedding performance after event ends
    """
    # 1. Get all telemetry during event
    event_telemetry = await get_telemetry_range(ven_id, event_start, event_end)
    
    if not event_telemetry:
        raise ValueError(f"No telemetry data for event {event_id}")
    
    # 2. Calculate baseline using pre-event data
    pre_event_data = await get_telemetry_range(
        ven_id, 
        event_start - 3600,  # 1 hour before
        event_start
    )
    baseline_kw = calculate_baseline_power(pre_event_data, event_start)
    baseline_confidence = assess_baseline_confidence(pre_event_data)
    
    # 3. Calculate actual average power during event
    actual_powers = [t.used_power_kw for t in event_telemetry]
    avg_actual_kw = sum(actual_powers) / len(actual_powers)
    
    # 4. Calculate shed metrics
    achieved_reduction_kw = baseline_kw - avg_actual_kw
    shed_percentage = (achieved_reduction_kw / event["requested_kw"]) * 100
    
    # 5. Calculate energy delivered (kWh)
    duration_hours = (event_end - event_start) / 3600.0
    delivered_kwh = achieved_reduction_kw * duration_hours
    
    # 6. Store performance metrics
    performance = EventPerformance(
        ven_id=ven_id,
        event_id=event_id,
        event_start_ts=event_start,
        event_end_ts=event_end,
        baseline_kw=baseline_kw,
        requested_reduction_kw=event["requested_kw"],
        target_kw=baseline_kw - event["requested_kw"],
        avg_actual_kw=avg_actual_kw,
        achieved_reduction_kw=achieved_reduction_kw,
        shed_percentage=shed_percentage,
        delivered_kwh=delivered_kwh,
        baseline_confidence=baseline_confidence,
        data_points_count=len(event_telemetry)
    )
    
    await save_event_performance(performance)
    return performance


def assess_baseline_confidence(pre_event_data: List) -> str:
    """
    Assess confidence in baseline calculation
    
    Returns: "high", "medium", or "low"
    """
    data_count = len(pre_event_data)
    
    # High confidence: 60+ minutes of data (12+ samples at 5min intervals)
    if data_count >= 12:
        variance = calculate_variance(pre_event_data)
        if variance < 2.0:  # Stable power consumption
            return "high"
        return "medium"
    
    # Medium confidence: 20-60 minutes of data
    if data_count >= 4:
        return "medium"
    
    # Low confidence: Less than 20 minutes
    return "low"
```

#### 4. Backend API Endpoints
**New endpoints for event performance analysis**:

```python
# In ecs-backend/app/routers/events.py

@router.get("/events/{event_id}/performance")
async def get_event_performance(
    event_id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Get performance metrics for a completed event
    
    Response includes:
    - Baseline calculation
    - Actual shed achieved
    - Percentage of target
    - Energy delivered (kWh)
    - Confidence metrics
    """
    performance = await get_event_performance_from_db(session, event_id)
    if not performance:
        raise HTTPException(404, "Event performance data not found")
    return performance


@router.get("/vens/{ven_id}/baseline")
async def get_ven_baseline(
    ven_id: str,
    timestamp: Optional[int] = None,
    session: AsyncSession = Depends(get_session)
):
    """
    Get current or historical baseline power estimate for a VEN
    
    Query params:
    - timestamp: Calculate baseline as of this time (default: now)
    
    Returns:
    - baseline_kw: Estimated baseline power
    - confidence: Confidence level
    - method: Which calculation method was used
    - data_points: Number of historical samples used
    """
    if timestamp is None:
        timestamp = int(time.time())
    
    historical_data = await get_ven_telemetry_history(
        session, ven_id, 
        start=timestamp - 86400,  # Last 24 hours
        end=timestamp
    )
    
    baseline = calculate_baseline_power(historical_data, timestamp)
    confidence = assess_baseline_confidence(historical_data)
    
    return {
        "ven_id": ven_id,
        "timestamp": timestamp,
        "baseline_kw": baseline,
        "confidence": confidence,
        "data_points": len(historical_data),
        "method": detect_baseline_method(historical_data, timestamp)
    }


@router.get("/vens/{ven_id}/shed-capacity")
async def estimate_shed_capacity(
    ven_id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Estimate the maximum load shedding capacity for a VEN
    
    Returns:
    - current_load_kw: Current power consumption
    - baseline_kw: Typical baseline
    - essential_load_kw: Estimated essential loads
    - available_shed_kw: current_load - essential
    - circuits: List of sheddable circuits with priorities
    """
    # Get current state
    latest_telemetry = await get_latest_telemetry(session, ven_id)
    baseline = await calculate_current_baseline(session, ven_id)
    
    # Analyze circuits
    circuits = await get_ven_circuits(session, ven_id)
    sheddable_circuits = []
    essential_load_kw = 0.0
    
    for circuit in circuits:
        if circuit.get("essential", False):
            essential_load_kw += circuit.get("current_kw", 0.0)
        else:
            sheddable_circuits.append({
                "id": circuit["id"],
                "name": circuit["name"],
                "current_kw": circuit.get("current_kw", 0.0),
                "priority": circuit.get("priority", 5)
            })
    
    available_shed_kw = latest_telemetry.used_power_kw - essential_load_kw
    
    return {
        "ven_id": ven_id,
        "current_load_kw": latest_telemetry.used_power_kw,
        "baseline_kw": baseline,
        "essential_load_kw": essential_load_kw,
        "available_shed_kw": max(0, available_shed_kw),
        "sheddable_circuits": sorted(sheddable_circuits, 
                                     key=lambda x: x["priority"])
    }
```

## Network Connectivity Issues

### Problem
VOLTTRON VEN cannot connect to AWS IoT Core:
```
MQTT connect failed (try 5/5): [Errno 101] Network is unreachable
```

### Possible Causes
1. **Security Group Configuration**
   - VPC endpoint for IoT Core might not allow access from VOLTTRON VEN security group
   - Missing egress rules for port 8883 (MQTTS)

2. **VPC Endpoint Configuration**
   - IoT Core VPC endpoint might not be properly configured
   - DNS resolution issues

3. **Network ACLs**
   - Network ACLs might be blocking outbound HTTPS/MQTTS traffic

### Resolution Steps
1. Check VOLTTRON VEN security group has egress rules for:
   - Port 8883 (MQTTS) to IoT Core endpoint
   - Port 443 (HTTPS) for AWS APIs

2. Verify IoT Core VPC endpoint exists and is accessible:
   ```bash
   aws ec2 describe-vpc-endpoints --region us-west-2 \
     --filters Name=service-name,Values=com.amazonaws.us-west-2.iot.data
   ```

3. Check VPC endpoint security group allows inbound on port 8883 from VEN security group

4. Verify VOLTTRON task has proper network configuration (public IP or NAT gateway)

## Testing Strategy

### Once Network Issues Resolved:

1. **Telemetry Flow Test**
   ```bash
   # Monitor backend MQTT consumer logs
   aws logs tail /ecs/ecs-backend --follow --filter-pattern "telemetry"
   
   # Check database for new telemetry
   psql -c "SELECT ven_id, timestamp, used_power_kw FROM ven_telemetry ORDER BY timestamp DESC LIMIT 10;"
   ```

2. **Auto-Registration Test**
   ```bash
   # Check if volttron_thing was auto-registered
   curl https://backend-alb.../api/vens/ | jq '.[] | select(.ven_id=="volttron_thing")'
   ```

3. **Load Shedding Test**
   ```bash
   # Send test event via backend command topic
   python scripts/send_event.py --ven-id volttron_thing --shed-kw 2.0 --duration 300
   
   # Monitor VOLTTRON response
   aws logs tail /ecs/volttron-ven --follow --filter-pattern "shed"
   
   # Check telemetry reflects reduced power
   curl https://backend-alb.../api/vens/volttron_thing/latest
   ```

4. **Performance Calculation Test**
   ```bash
   # After event ends, calculate performance
   curl https://backend-alb.../api/events/{event_id}/performance
   
   # Verify metrics match expectations
   ```

## Future Enhancements

1. **Machine Learning Baseline Prediction**
   - Train ML model on historical data
   - Predict baseline based on time, day, weather, etc.
   - Improve accuracy for events scheduled days in advance

2. **Predictive Load Shedding**
   - Preemptive load reduction before event starts
   - Leverage thermal storage (HVAC, water heater)
   - Reduce perceived impact on occupants

3. **Multi-VEN Aggregation**
   - Portfolio-level load shedding orchestration
   - Optimal distribution of shed requests across VENs
   - Fairness and equity considerations

4. **Real-time Optimization**
   - Dynamic circuit selection during events
   - Respond to actual vs. target performance
   - Minimize occupant disruption while hitting targets

## References

- [OpenADR 2.0b Specification](https://www.openadr.org/specification)
- [AWS IoT Core Documentation](https://docs.aws.amazon.com/iot/latest/developerguide/)
- [MQTT v3.1.1 Protocol](https://docs.oasis-open.org/mqtt/mqtt/v3.1.1/mqtt-v3.1.1.html)
