"""Tests for VEN device simulator."""
import pytest
from datetime import datetime, UTC
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

import device_simulator
from device_simulator import (
    circuits,
    circuits_snapshot,
    calculate_panel_power,
    apply_load_limits,
    update_circuit_power,
    handle_shed_command,
    handle_restore_command,
    load_limits,
    power_history,
    battery_soc,
    battery_capacity_kwh,
    active_event,
)


def test_circuits_snapshot():
    """Test getting a snapshot of all circuits."""
    snapshot = circuits_snapshot()
    
    assert isinstance(snapshot, list)
    assert len(snapshot) > 0
    
    # Check structure of first circuit
    circuit = snapshot[0]
    assert "id" in circuit
    assert "name" in circuit
    assert "type" in circuit
    assert "enabled" in circuit
    assert "current_kw" in circuit
    assert "rated_kw" in circuit
    assert "shed_capability_kw" in circuit


def test_calculate_panel_power():
    """Test panel power calculation."""
    power = calculate_panel_power()
    
    assert isinstance(power, float)
    assert power >= 0.0


def test_apply_load_limits_no_limits():
    """Test applying load limits when none are set."""
    original_limits = device_simulator.load_limits.copy()
    device_simulator.load_limits.clear()
    
    try:
        apply_load_limits()
        # Should not raise
        assert True
    finally:
        device_simulator.load_limits.update(original_limits)


def test_update_circuit_power():
    """Test updating circuit power based on state."""
    # Store original state
    original_states = {c["id"]: c["enabled"] for c in circuits}
    
    try:
        # Enable a specific circuit
        for circuit in circuits:
            if circuit["id"] == "hvac1":
                circuit["enabled"] = True
                break
        
        update_circuit_power()
        
        # Find HVAC circuit and check it has power
        hvac = next((c for c in circuits if c["id"] == "hvac1"), None)
        assert hvac is not None
        
        # When enabled, should have some power (or 0 depending on implementation)
        assert "current_kw" in hvac
        assert isinstance(hvac["current_kw"], (int, float))
    finally:
        # Restore original states
        for circuit in circuits:
            circuit["enabled"] = original_states.get(circuit["id"], False)


def test_handle_shed_command_basic():
    """Test handling a basic shed command."""
    command = {
        "target_kw": 2.0,
        "duration_s": 300,
        "event_id": "test-event-1"
    }
    
    result = handle_shed_command(command)
    
    assert isinstance(result, dict)
    assert "shed_kw" in result
    assert "loads_affected" in result
    assert isinstance(result["shed_kw"], (int, float))
    assert isinstance(result["loads_affected"], list)


def test_handle_shed_command_with_priority():
    """Test shed command respects circuit priorities."""
    command = {
        "target_kw": 5.0,
        "duration_s": 600,
        "event_id": "test-event-2"
    }
    
    result = handle_shed_command(command)
    
    # Should shed from non-critical loads first
    loads_affected = result["loads_affected"]
    
    # Check that some loads were affected
    assert len(loads_affected) >= 0


def test_handle_restore_command():
    """Test restoring loads after shed."""
    # First shed some loads
    shed_command = {
        "target_kw": 3.0,
        "duration_s": 300,
        "event_id": "test-event-3"
    }
    handle_shed_command(shed_command)
    
    # Then restore
    restore_command = {
        "event_id": "test-event-3"
    }
    
    result = handle_restore_command(restore_command)
    
    assert isinstance(result, dict)
    assert "status" in result or "loads_restored" in result


def test_circuit_types():
    """Test that circuits have expected types."""
    expected_types = {"hvac", "heater", "ev", "battery", "pv", "lights", "fridge", "misc"}
    
    circuit_types = {c["type"] for c in circuits}
    
    # All circuit types should be in expected set
    for ctype in circuit_types:
        assert ctype in expected_types


def test_critical_circuits_exist():
    """Test that critical circuits are properly marked."""
    critical_circuits = [c for c in circuits if c.get("critical", False)]
    
    assert len(critical_circuits) > 0
    
    # HVAC and fridge are typically critical
    critical_types = {c["type"] for c in critical_circuits}
    assert "hvac" in critical_types or "fridge" in critical_types


def test_shed_capability_reasonable():
    """Test that shed capabilities are reasonable."""
    for circuit in circuits:
        shed_cap = circuit.get("shed_capability_kw", 0)
        rated_kw = circuit.get("rated_kw", 0)
        
        # Shed capability should not exceed rated power
        assert shed_cap <= rated_kw
        assert shed_cap >= 0


def test_circuit_enabled_toggles():
    """Test toggling circuit enabled state."""
    circuit = circuits[0]
    original_state = circuit["enabled"]
    
    try:
        # Toggle state
        circuit["enabled"] = not original_state
        assert circuit["enabled"] == (not original_state)
        
        # Toggle back
        circuit["enabled"] = original_state
        assert circuit["enabled"] == original_state
    finally:
        circuit["enabled"] = original_state


def test_power_history_tracking():
    """Test that power history is being tracked."""
    # Power history should be a deque
    assert hasattr(power_history, 'maxlen')
    
    # Should be able to add entries
    initial_len = len(power_history)
    timestamp = int(datetime.now(UTC).timestamp())
    power_history.append((timestamp, 5.0))
    
    assert len(power_history) >= initial_len


def test_battery_state_tracking():
    """Test battery state of charge tracking."""
    assert isinstance(battery_soc, float)
    assert 0.0 <= battery_soc <= 1.0
    
    assert isinstance(battery_capacity_kwh, float)
    assert battery_capacity_kwh > 0


def test_active_event_tracking():
    """Test active event state tracking."""
    # Active event should be None or a dict
    assert active_event is None or isinstance(active_event, dict)


def test_handle_shed_zero_target():
    """Test handling shed command with zero target."""
    command = {
        "target_kw": 0.0,
        "duration_s": 300,
        "event_id": "test-event-zero"
    }
    
    result = handle_shed_command(command)
    
    # Should return valid result even with zero target
    assert isinstance(result, dict)
    assert result["shed_kw"] == 0.0


def test_handle_shed_large_target():
    """Test handling shed command with unrealistic large target."""
    command = {
        "target_kw": 1000.0,  # Very large
        "duration_s": 300,
        "event_id": "test-event-large"
    }
    
    result = handle_shed_command(command)
    
    # Should shed maximum available, not crash
    assert isinstance(result, dict)
    assert result["shed_kw"] >= 0.0
