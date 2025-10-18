#!/usr/bin/env python3
"""
Enhanced Local VEN with:
1. Device Shadow sync
2. Local web UI for control
3. DR event handling with load curtailment
"""
import os
import json
import time
import random
import ssl
import threading
from datetime import datetime
from flask import Flask, render_template_string, jsonify, request
import paho.mqtt.client as mqtt

# Configuration from environment
IOT_ENDPOINT = os.getenv("IOT_ENDPOINT")
CLIENT_ID = os.getenv("CLIENT_ID", "volttron_local")
CA_CERT = os.getenv("CA_CERT", "./certs/ca.pem")
CLIENT_CERT = os.getenv("CLIENT_CERT", "./certs/client.crt")
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "./certs/client.key")
TELEMETRY_TOPIC = os.getenv("TELEMETRY_TOPIC", f"ven/telemetry/{CLIENT_ID}")
METERING_TOPIC = os.getenv("METERING_TOPIC", f"oadr/meter/{CLIENT_ID}")
CMD_TOPIC = os.getenv("CMD_TOPIC", f"ven/cmd/{CLIENT_ID}")
ACK_TOPIC = os.getenv("ACK_TOPIC", f"ven/ack/{CLIENT_ID}")
WEB_PORT = int(os.getenv("WEB_PORT", "8080"))

# Device Shadow topics
SHADOW_UPDATE_TOPIC = f"$aws/things/{CLIENT_ID}/shadow/update"
SHADOW_GET_TOPIC = f"$aws/things/{CLIENT_ID}/shadow/get"
SHADOW_DELTA_TOPIC = f"$aws/things/{CLIENT_ID}/shadow/update/delta"

# ============================================================================
# STATE MANAGEMENT
# ============================================================================

state_lock = threading.Lock()

# Circuit definitions (from device_simulator.py)
circuits = [
    {"id": "hvac1", "name": "HVAC", "type": "hvac", "enabled": True, "connected": True, 
     "rated_kw": 3.5, "current_kw": 0.0, "critical": True, "mode": "dynamic"},
    {"id": "heater1", "name": "Heater", "type": "heater", "enabled": True, "connected": True,
     "rated_kw": 1.5, "current_kw": 0.0, "critical": False, "mode": "dynamic"},
    {"id": "ev1", "name": "EV Charger", "type": "ev", "enabled": False, "connected": True,
     "rated_kw": 7.2, "current_kw": 0.0, "critical": False, "mode": "dynamic"},
    {"id": "lights1", "name": "Lights", "type": "lights", "enabled": True, "connected": True,
     "rated_kw": 0.4, "current_kw": 0.0, "critical": False, "mode": "dynamic"},
    {"id": "fridge1", "name": "Fridge", "type": "fridge", "enabled": True, "connected": True,
     "rated_kw": 0.2, "current_kw": 0.0, "critical": True, "mode": "dynamic"},
    {"id": "misc1", "name": "House Load", "type": "misc", "enabled": True, "connected": True,
     "rated_kw": 1.0, "current_kw": 0.0, "critical": False, "mode": "dynamic"},
]

# Global state
ven_state = {
    "connected": False,
    "message_count": 0,
    "base_power_kw": 10.0,  # Base power before any curtailment
    "current_power_kw": 10.0,
    "shed_kw": 0.0,
    "active_event": None,  # {"event_id": "evt-123", "shed_kw": 2.0, "end_ts": 123456}
    "circuits": circuits,
    "last_shadow_update": None,
}

# Power history for baseline calculation (last 30 minutes at 5-second intervals = 360 samples)
from collections import deque
power_history: deque = deque(maxlen=360)

mqtt_client = None

# ============================================================================
# POWER SIMULATION
# ============================================================================

def calculate_total_power():
    """Calculate total power from enabled circuits"""
    with state_lock:
        total = sum(c["current_kw"] for c in circuits if c.get("enabled", True))
        return round(total, 2)

def distribute_power_to_circuits(total_kw):
    """Distribute total power among enabled circuits by rated_kw proportion"""
    with state_lock:
        enabled = [c for c in circuits if c.get("enabled", True) and c.get("rated_kw", 0.0) > 0]
        if not enabled or total_kw <= 0:
            for c in circuits:
                c["current_kw"] = 0.0
            return
        
        weight_sum = sum(c["rated_kw"] for c in enabled)
        for c in enabled:
            share = c["rated_kw"] / weight_sum if weight_sum > 0 else 0.0
            c["current_kw"] = round(total_kw * share, 2)
        
        for c in circuits:
            if c not in enabled:
                c["current_kw"] = 0.0

def simulate_base_power():
    """Simulate base power with slight jitter"""
    with state_lock:
        jitter = random.uniform(-0.5, 0.5)
        ven_state["base_power_kw"] = round(ven_state["base_power_kw"] + jitter, 2)
        # Keep between 8-12 kW
        ven_state["base_power_kw"] = max(8.0, min(12.0, ven_state["base_power_kw"]))
        return ven_state["base_power_kw"]

# ============================================================================
# DR EVENT HANDLING
# ============================================================================

def apply_curtailment(shed_kw):
    """Apply load curtailment to meet shed_kw target
    
    Strategy:
    1. Shed non-critical loads first (heater, lights, misc, EV)
    2. If needed, reduce critical loads (HVAC, fridge) to 80% of rated
    """
    with state_lock:
        target_shed = shed_kw
        actual_shed = 0.0
        
        # Priority order for shedding (non-critical first)
        shed_order = [
            ("heater1", 1.0),   # Can shed 100% of heater
            ("lights1", 0.7),   # Can shed 70% of lights
            ("misc1", 0.6),     # Can shed 60% of house load
            ("ev1", 1.0),       # Can shed 100% of EV
            ("hvac1", 0.2),     # Can shed 20% of HVAC (critical, keep 80%)
            ("fridge1", 0.2),   # Can shed 20% of fridge (critical, keep 80%)
        ]
        
        # Store original power for restoration
        original_power = {c["id"]: c["current_kw"] for c in circuits}
        
        for circuit_id, max_shed_ratio in shed_order:
            if actual_shed >= target_shed:
                break
            
            circuit = next((c for c in circuits if c["id"] == circuit_id), None)
            if not circuit or not circuit.get("enabled"):
                continue
            
            current_kw = circuit["current_kw"]
            max_shed_kw = current_kw * max_shed_ratio
            shed_amount = min(max_shed_kw, target_shed - actual_shed)
            
            if shed_amount > 0:
                circuit["current_kw"] = round(current_kw - shed_amount, 2)
                actual_shed = round(actual_shed + shed_amount, 2)
                print(f"  🔻 Shed {shed_amount:.2f} kW from {circuit['name']}")
        
        ven_state["shed_kw"] = actual_shed
        ven_state["current_power_kw"] = round(ven_state["base_power_kw"] - actual_shed, 2)
        
        print(f"✅ Curtailment applied: {actual_shed:.2f} kW shed (target: {target_shed:.2f} kW)")
        return actual_shed

def restore_circuits():
    """Restore all circuits to normal operation"""
    with state_lock:
        distribute_power_to_circuits(ven_state["base_power_kw"])
        ven_state["shed_kw"] = 0.0
        ven_state["current_power_kw"] = ven_state["base_power_kw"]
        ven_state["active_event"] = None
        print("✅ All circuits restored to normal operation")

# ============================================================================
# DEVICE SHADOW
# ============================================================================

def publish_shadow_update():
    """Publish current state to device shadow"""
    if not mqtt_client or not ven_state["connected"]:
        return
    
    with state_lock:
        reported = {
            "power_kw": ven_state["current_power_kw"],
            "shed_kw": ven_state["shed_kw"],
            "base_power_kw": ven_state["base_power_kw"],
            "circuits": [
                {
                    "id": c["id"],
                    "name": c["name"],
                    "enabled": c["enabled"],
                    "current_kw": c["current_kw"],
                    "critical": c["critical"]
                }
                for c in circuits
            ],
            "active_event": ven_state["active_event"],
            "timestamp": int(time.time())
        }
    
    shadow_doc = {
        "state": {
            "reported": reported
        }
    }
    
    try:
        mqtt_client.publish(SHADOW_UPDATE_TOPIC, json.dumps(shadow_doc), qos=1)
        ven_state["last_shadow_update"] = int(time.time())
        print(f"📤 Shadow updated: {ven_state['current_power_kw']:.2f} kW, shed: {ven_state['shed_kw']:.2f} kW")
    except Exception as e:
        print(f"❌ Shadow update failed: {e}")

def handle_shadow_delta(payload):
    """Handle shadow delta (desired vs reported state difference)"""
    try:
        state = payload.get("state", {})
        
        # Handle circuit enable/disable from shadow desired state
        if "circuits" in state:
            with state_lock:
                for desired_circuit in state["circuits"]:
                    circuit_id = desired_circuit.get("id")
                    circuit = next((c for c in circuits if c["id"] == circuit_id), None)
                    if circuit and "enabled" in desired_circuit:
                        circuit["enabled"] = desired_circuit["enabled"]
                        print(f"🔄 Circuit {circuit['name']} {'enabled' if circuit['enabled'] else 'disabled'} via shadow")
            
            # Recalculate power distribution
            distribute_power_to_circuits(ven_state["base_power_kw"] - ven_state["shed_kw"])
            publish_shadow_update()
            
    except Exception as e:
        print(f"❌ Shadow delta error: {e}")

# ============================================================================
# MQTT CALLBACKS
# ============================================================================

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        ven_state["connected"] = True
        print(f"✅ Connected to AWS IoT Core (client_id={CLIENT_ID})")
        
        # Subscribe to topics
        client.subscribe(CMD_TOPIC, qos=1)
        print(f"📡 Subscribed: {CMD_TOPIC}")
        
        client.subscribe(SHADOW_DELTA_TOPIC, qos=1)
        print(f"📡 Subscribed: {SHADOW_DELTA_TOPIC}")
        
        # Request current shadow
        client.publish(SHADOW_GET_TOPIC, "", qos=1)
        print(f"📥 Requested current shadow")
        
    else:
        ven_state["connected"] = False
        print(f"❌ Connection failed with code {rc}")

def on_disconnect(client, userdata, rc):
    ven_state["connected"] = False
    if rc == 0:
        print("🔌 Disconnected (graceful)")
    else:
        print(f"⚠️  Disconnected unexpectedly (rc={rc})")

def on_message(client, userdata, msg):
    """Handle incoming MQTT messages"""
    try:
        # Handle shadow delta
        if msg.topic == SHADOW_DELTA_TOPIC:
            payload = json.loads(msg.payload.decode())
            print(f"📨 Shadow delta received")
            handle_shadow_delta(payload)
            return
        
        # Handle commands
        if msg.topic == CMD_TOPIC:
            payload = json.loads(msg.payload.decode())
            print(f"📨 Command received: {payload.get('op')}")
            handle_command(client, payload)
            return
            
    except Exception as e:
        print(f"❌ Error processing message: {e}")

def calculate_baseline():
    """Calculate baseline power from recent history (pre-event average)."""
    if len(power_history) < 12:  # Need at least 1 minute of history
        return ven_state["base_power_kw"]
    
    # Use average of last 5 minutes before event (60 samples)
    recent_samples = list(power_history)[-60:]
    if recent_samples:
        return round(sum(s[1] for s in recent_samples) / len(recent_samples), 2)
    return ven_state["base_power_kw"]

def handle_command(client, payload):
    """Handle incoming commands"""
    op = payload.get("op")
    corr_id = payload.get("correlationId")
    
    if op == "ping":
        ack = {
            "op": "ping",
            "status": "success",
            "pong": True,
            "ts": int(time.time()),
            "correlationId": corr_id
        }
        client.publish(ACK_TOPIC, json.dumps(ack), qos=1)
        print(f"✅ Pong sent")
    
    elif op in ["event", "shedPanel"]:
        # DR event with load curtailment (supports both 'event' and 'shedPanel' ops)
        # Extract shed amount from various possible fields
        shed_kw = float(
            payload.get("shed_kw") or 
            payload.get("data", {}).get("requestedReductionKw") or 
            payload.get("requestedReductionKw") or 
            0.0
        )
        
        # Extract duration
        duration_sec = int(
            payload.get("duration_sec") or 
            payload.get("data", {}).get("duration_s") or 
            payload.get("duration_s") or 
            3600
        )
        
        # Extract event ID
        event_id = (
            payload.get("event_id") or 
            payload.get("data", {}).get("event_id") or 
            f"evt-{int(time.time())}"
        )
        
        print(f"\n🚨 DR EVENT RECEIVED")
        print(f"   Event ID: {event_id}")
        print(f"   Shed: {shed_kw:.2f} kW")
        print(f"   Duration: {duration_sec} seconds")
        
        # Apply curtailment
        actual_shed = apply_curtailment(shed_kw)
        
        # Track active event
        ven_state["active_event"] = {
            "event_id": event_id,
            "shed_kw": shed_kw,
            "actual_shed_kw": actual_shed,
            "end_ts": int(time.time()) + duration_sec
        }
        
        # Update shadow
        publish_shadow_update()
        
        # Send acknowledgment
        ack = {
            "op": "event",
            "status": "accepted",
            "event_id": event_id,
            "requested_shed_kw": shed_kw,
            "actual_shed_kw": actual_shed,
            "ts": int(time.time()),
            "correlationId": corr_id
        }
        client.publish(ACK_TOPIC, json.dumps(ack), qos=1)
        print(f"✅ Event acknowledged\n")
    
    elif op == "restore":
        # Restore normal operation
        print("\n🔄 RESTORE COMMAND RECEIVED")
        restore_circuits()
        publish_shadow_update()
        
        ack = {
            "op": "restore",
            "status": "success",
            "ts": int(time.time()),
            "correlationId": corr_id
        }
        client.publish(ACK_TOPIC, json.dumps(ack), qos=1)
        print(f"✅ Restoration acknowledged\n")

# ============================================================================
# WEB UI
# ============================================================================

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>VEN Local Control</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: #0f172a; color: #e2e8f0; padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { margin-bottom: 10px; color: #38bdf8; }
        .subtitle { color: #94a3b8; margin-bottom: 30px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .card { background: #1e293b; border-radius: 12px; padding: 20px; border: 1px solid #334155; }
        .card h2 { font-size: 18px; margin-bottom: 15px; color: #38bdf8; }
        .stat { margin-bottom: 12px; }
        .stat-label { font-size: 14px; color: #94a3b8; }
        .stat-value { font-size: 24px; font-weight: 600; }
        .stat-value.power { color: #22c55e; }
        .stat-value.shed { color: #f59e0b; }
        .status { display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; }
        .status.connected { background: #065f46; color: #6ee7b7; }
        .status.disconnected { background: #7f1d1d; color: #fca5a5; }
        .circuit { 
            background: #0f172a; padding: 12px; border-radius: 8px; margin-bottom: 10px;
            display: flex; justify-content: space-between; align-items: center;
        }
        .circuit-info { flex: 1; }
        .circuit-name { font-weight: 600; }
        .circuit-power { color: #94a3b8; font-size: 14px; }
        .circuit-critical { color: #f59e0b; font-size: 12px; margin-left: 8px; }
        .toggle { position: relative; width: 48px; height: 24px; }
        .toggle input { opacity: 0; width: 0; height: 0; }
        .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0;
                  background-color: #334155; border-radius: 24px; transition: 0.3s; }
        .slider:before { position: absolute; content: ""; height: 18px; width: 18px; left: 3px;
                         bottom: 3px; background-color: white; border-radius: 50%; transition: 0.3s; }
        input:checked + .slider { background-color: #22c55e; }
        input:checked + .slider:before { transform: translateX(24px); }
        .event-card { background: #7f1d1d; border-color: #991b1b; }
        .event-card h2 { color: #fca5a5; }
        .btn { 
            padding: 10px 20px; border: none; border-radius: 8px; font-weight: 600;
            cursor: pointer; font-size: 14px; margin-right: 10px; margin-top: 10px;
        }
        .btn-primary { background: #2563eb; color: white; }
        .btn-danger { background: #dc2626; color: white; }
        .btn-success { background: #16a34a; color: white; }
        .btn:hover { opacity: 0.9; }
        .input-group { margin-bottom: 15px; }
        .input-group label { display: block; margin-bottom: 5px; font-size: 14px; color: #94a3b8; }
        .input-group input { 
            width: 100%; padding: 8px 12px; border-radius: 6px; border: 1px solid #334155;
            background: #0f172a; color: #e2e8f0; font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚡ VEN Local Control Panel</h1>
        <p class="subtitle">Real-time monitoring and control</p>
        
        <div class="grid">
            <div class="card">
                <h2>📊 Power Status</h2>
                <div class="stat">
                    <div class="stat-label">Connection</div>
                    <div>
                        <span class="status" id="conn-status">Disconnected</span>
                    </div>
                </div>
                <div class="stat">
                    <div class="stat-label">Current Power</div>
                    <div class="stat-value power" id="current-power">-- kW</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Load Shed</div>
                    <div class="stat-value shed" id="shed-power">-- kW</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Base Power</div>
                    <div class="stat-value" id="base-power">-- kW</div>
                </div>
            </div>
            
            <div class="card" id="event-card">
                <h2>🚨 DR Event Control</h2>
                <div id="no-event">
                    <p style="color: #94a3b8; margin-bottom: 15px;">No active event</p>
                    <div class="input-group">
                        <label>Shed Amount (kW)</label>
                        <input type="number" id="shed-input" value="2.0" step="0.1" min="0">
                    </div>
                    <div class="input-group">
                        <label>Duration (seconds)</label>
                        <input type="number" id="duration-input" value="300" step="60" min="60">
                    </div>
                    <button class="btn btn-danger" onclick="triggerEvent()">🚨 Trigger DR Event</button>
                </div>
                <div id="active-event" style="display: none;">
                    <div class="stat">
                        <div class="stat-label">Event ID</div>
                        <div id="event-id" style="font-size: 14px;">--</div>
                    </div>
                    <div class="stat">
                        <div class="stat-label">Requested Shed</div>
                        <div id="event-shed">-- kW</div>
                    </div>
                    <div class="stat">
                        <div class="stat-label">Time Remaining</div>
                        <div id="event-time">--</div>
                    </div>
                    <button class="btn btn-success" onclick="restoreNormal()">✅ Restore Normal</button>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>🔌 Circuits</h2>
            <div id="circuits-list"></div>
        </div>
    </div>
    
    <script>
        function fetchState() {
            fetch('/api/state')
                .then(r => r.json())
                .then(data => {
                    // Update connection status
                    const connStatus = document.getElementById('conn-status');
                    if (data.connected) {
                        connStatus.className = 'status connected';
                        connStatus.textContent = 'Connected';
                    } else {
                        connStatus.className = 'status disconnected';
                        connStatus.textContent = 'Disconnected';
                    }
                    
                    // Update power stats
                    document.getElementById('current-power').textContent = data.current_power_kw.toFixed(2) + ' kW';
                    document.getElementById('shed-power').textContent = data.shed_kw.toFixed(2) + ' kW';
                    document.getElementById('base-power').textContent = data.base_power_kw.toFixed(2) + ' kW';
                    
                    // Update event status
                    const eventCard = document.getElementById('event-card');
                    const noEvent = document.getElementById('no-event');
                    const activeEvent = document.getElementById('active-event');
                    
                    if (data.active_event) {
                        eventCard.className = 'card event-card';
                        noEvent.style.display = 'none';
                        activeEvent.style.display = 'block';
                        document.getElementById('event-id').textContent = data.active_event.event_id;
                        document.getElementById('event-shed').textContent = data.active_event.shed_kw.toFixed(2) + ' kW';
                        const remaining = Math.max(0, data.active_event.end_ts - Math.floor(Date.now() / 1000));
                        document.getElementById('event-time').textContent = remaining + ' seconds';
                    } else {
                        eventCard.className = 'card';
                        noEvent.style.display = 'block';
                        activeEvent.style.display = 'none';
                    }
                    
                    // Update circuits
                    const circuitsList = document.getElementById('circuits-list');
                    circuitsList.innerHTML = data.circuits.map(c => `
                        <div class="circuit">
                            <div class="circuit-info">
                                <div>
                                    <span class="circuit-name">${c.name}</span>
                                    ${c.critical ? '<span class="circuit-critical">⚠️ Critical</span>' : ''}
                                </div>
                                <div class="circuit-power">${c.current_kw.toFixed(2)} kW / ${c.rated_kw.toFixed(1)} kW rated</div>
                            </div>
                            <label class="toggle">
                                <input type="checkbox" ${c.enabled ? 'checked' : ''} 
                                       onchange="toggleCircuit('${c.id}', this.checked)">
                                <span class="slider"></span>
                            </label>
                        </div>
                    `).join('');
                });
        }
        
        function toggleCircuit(circuitId, enabled) {
            fetch('/api/circuit/toggle', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({circuit_id: circuitId, enabled: enabled})
            }).then(r => r.json()).then(data => {
                if (data.status === 'success') {
                    console.log('Circuit toggled:', circuitId, enabled);
                }
            });
        }
        
        function triggerEvent() {
            const shedKw = parseFloat(document.getElementById('shed-input').value);
            const duration = parseInt(document.getElementById('duration-input').value);
            
            fetch('/api/event/trigger', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({shed_kw: shedKw, duration_sec: duration})
            }).then(r => r.json()).then(data => {
                if (data.status === 'success') {
                    console.log('Event triggered');
                    fetchState();
                }
            });
        }
        
        function restoreNormal() {
            fetch('/api/event/restore', {method: 'POST'})
                .then(r => r.json())
                .then(data => {
                    if (data.status === 'success') {
                        console.log('Restored to normal');
                        fetchState();
                    }
                });
        }
        
        // Auto-refresh every 2 seconds
        setInterval(fetchState, 2000);
        fetchState();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/state')
def api_state():
    with state_lock:
        return jsonify(ven_state)

@app.route('/api/circuit/toggle', methods=['POST'])
def api_toggle_circuit():
    data = request.json
    circuit_id = data.get('circuit_id')
    enabled = data.get('enabled', True)
    
    with state_lock:
        circuit = next((c for c in circuits if c["id"] == circuit_id), None)
        if circuit:
            circuit["enabled"] = enabled
            print(f"🔄 Circuit {circuit['name']} {'enabled' if enabled else 'disabled'} via UI")
            
            # Recalculate power
            if ven_state["active_event"]:
                # Re-apply curtailment
                apply_curtailment(ven_state["active_event"]["shed_kw"])
            else:
                distribute_power_to_circuits(ven_state["base_power_kw"])
            
            publish_shadow_update()
            return jsonify({"status": "success"})
    
    return jsonify({"status": "error", "message": "Circuit not found"}), 404

@app.route('/api/event/trigger', methods=['POST'])
def api_trigger_event():
    data = request.json
    shed_kw = float(data.get('shed_kw', 0.0))
    duration_sec = int(data.get('duration_sec', 300))
    
    print(f"\n🚨 DR EVENT TRIGGERED VIA UI")
    print(f"   Shed: {shed_kw:.2f} kW")
    print(f"   Duration: {duration_sec} seconds")
    
    # Apply curtailment
    actual_shed = apply_curtailment(shed_kw)
    
    # Track active event
    event_id = f"ui-evt-{int(time.time())}"
    ven_state["active_event"] = {
        "event_id": event_id,
        "shed_kw": shed_kw,
        "actual_shed_kw": actual_shed,
        "end_ts": int(time.time()) + duration_sec
    }
    
    publish_shadow_update()
    
    return jsonify({"status": "success", "event_id": event_id, "actual_shed_kw": actual_shed})

@app.route('/api/event/restore', methods=['POST'])
def api_restore():
    print("\n🔄 RESTORE TRIGGERED VIA UI")
    restore_circuits()
    publish_shadow_update()
    return jsonify({"status": "success"})

def run_web_server():
    """Run Flask web server in a separate thread"""
    print(f"🌐 Starting web UI on http://localhost:{WEB_PORT}")
    app.run(host='0.0.0.0', port=WEB_PORT, debug=False, use_reloader=False)

# ============================================================================
# MAIN LOOP
# ============================================================================

def telemetry_loop():
    """Main telemetry publishing loop"""
    global mqtt_client
    
    while True:
        try:
            if ven_state["connected"]:
                # Check if event has expired
                if ven_state["active_event"]:
                    if int(time.time()) >= ven_state["active_event"]["end_ts"]:
                        print("\n⏰ Event duration expired, restoring normal operation")
                        restore_circuits()
                
                # Simulate base power changes
                simulate_base_power()
                
                # Distribute power to circuits (respecting current curtailment)
                if ven_state["active_event"]:
                    # Re-apply curtailment with new base power
                    apply_curtailment(ven_state["active_event"]["shed_kw"])
                else:
                    distribute_power_to_circuits(ven_state["base_power_kw"])
                
                # Track power history for baseline calculation
                current_ts = int(time.time())
                power_history.append((current_ts, ven_state["current_power_kw"]))
                
                # Calculate baseline if in event
                baseline_kw = calculate_baseline() if ven_state["active_event"] else ven_state["base_power_kw"]
                
                # Publish telemetry
                ven_state["message_count"] += 1
                telemetry = {
                    "venId": CLIENT_ID,
                    "timestamp": current_ts,
                    "usedPowerKw": ven_state["current_power_kw"],
                    "shedPowerKw": ven_state["shed_kw"],
                    "requestedReductionKw": ven_state["active_event"]["shed_kw"] if ven_state["active_event"] else 0.0,
                    "eventId": ven_state["active_event"]["event_id"] if ven_state["active_event"] else None,
                    "baselinePowerKw": baseline_kw,
                    "message_num": ven_state["message_count"],
                    # Legacy fields for backward compatibility
                    "power_kw": ven_state["current_power_kw"],
                    "shed_kw": ven_state["shed_kw"],
                    "base_power_kw": ven_state["base_power_kw"],
                    "ts": current_ts,
                    "active_event": ven_state["active_event"]["event_id"] if ven_state["active_event"] else None,
                }
                
                # Publish to both telemetry topics
                result1 = mqtt_client.publish(TELEMETRY_TOPIC, json.dumps(telemetry), qos=1)
                result2 = mqtt_client.publish(METERING_TOPIC, json.dumps(telemetry), qos=1)
                
                if result1.rc == mqtt.MQTT_ERR_SUCCESS and result2.rc == mqtt.MQTT_ERR_SUCCESS:
                    event_marker = f" [EVENT: {ven_state['active_event']['event_id']}]" if ven_state['active_event'] else ""
                    print(f"✓ [{ven_state['message_count']}] Telemetry: {ven_state['current_power_kw']:.2f} kW "
                          f"(shed: {ven_state['shed_kw']:.2f} kW){event_marker}")
                
                # Update shadow every 30 seconds
                if ven_state["message_count"] % 6 == 0:
                    publish_shadow_update()
            else:
                print("⚠️  Not connected, waiting...")
            
            time.sleep(5)
            
        except Exception as e:
            print(f"❌ Telemetry loop error: {e}")
            time.sleep(5)

def main():
    global mqtt_client
    
    print("🚀 Starting Enhanced Local VEN")
    print(f"   Endpoint: {IOT_ENDPOINT}")
    print(f"   Client ID: {CLIENT_ID}")
    print(f"   Web UI: http://localhost:{WEB_PORT}")
    print()
    
    # Verify certificates
    for cert_name, cert_path in [("CA", CA_CERT), ("Client", CLIENT_CERT), ("Key", PRIVATE_KEY)]:
        if not os.path.exists(cert_path):
            print(f"❌ {cert_name} certificate not found: {cert_path}")
            return 1
        print(f"✓ {cert_name} cert: {cert_path}")
    print()
    
    # Initialize power distribution
    distribute_power_to_circuits(ven_state["base_power_kw"])
    
    # Create MQTT client
    mqtt_client = mqtt.Client(client_id=CLIENT_ID, protocol=mqtt.MQTTv311)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_disconnect = on_disconnect
    mqtt_client.on_message = on_message
    
    # Configure TLS
    try:
        mqtt_client.tls_set(
            ca_certs=CA_CERT,
            certfile=CLIENT_CERT,
            keyfile=PRIVATE_KEY,
            cert_reqs=ssl.CERT_REQUIRED,
            tls_version=ssl.PROTOCOL_TLSv1_2
        )
        print("✓ TLS configured")
    except Exception as e:
        print(f"❌ TLS setup failed: {e}")
        return 1
    
    # Connect
    print(f"\n🔌 Connecting to {IOT_ENDPOINT}:8883...")
    try:
        mqtt_client.connect(IOT_ENDPOINT, 8883, keepalive=60)
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return 1
    
    # Start network loop
    mqtt_client.loop_start()
    
    # Start web server in separate thread
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    # Wait for connection
    print("⏳ Waiting for MQTT connection...")
    for i in range(10):
        if ven_state["connected"]:
            break
        time.sleep(1)
    
    if not ven_state["connected"]:
        print("❌ Failed to connect after 10 seconds")
        mqtt_client.loop_stop()
        return 1
    
    print("✅ MQTT connection established!\n")
    print("📊 Publishing telemetry every 5 seconds...")
    print(f"🌐 Web UI available at http://localhost:{WEB_PORT}")
    print("Press Ctrl+C to stop\n")
    
    # Run telemetry loop
    try:
        telemetry_loop()
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
    finally:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        print("👋 Goodbye!")
    
    return 0

if __name__ == "__main__":
    exit(main())
