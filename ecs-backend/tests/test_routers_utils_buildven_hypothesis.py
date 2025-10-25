import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from app.routers.utils import build_ven_payload
from app.models.ven import VEN
from app.models.telemetry import VenStatus, VenTelemetry
from datetime import datetime

@given(
    st.text(min_size=1, max_size=10),
    st.text(min_size=1, max_size=20),
    st.text(min_size=1, max_size=10),
    st.floats(min_value=-90, max_value=90),
    st.floats(min_value=-180, max_value=180),
    st.datetimes()
)
@settings(suppress_health_check=[HealthCheck.too_slow])
def test_build_ven_payload_property(ven_id, name, status, lat, lon, created_at):
    ven = VEN(ven_id=ven_id, name=name, status=status, latitude=lat, longitude=lon, created_at=created_at)
    # Minimal status and telemetry
    status_obj = VenStatus(status=status, current_power_kw=1.0, shed_availability_kw=2.0, active_event_id=None)
    telemetry_obj = VenTelemetry(timestamp=created_at, used_power_kw=1.0, shed_power_kw=2.0, event_id=None, loads=[])
    result = build_ven_payload(ven, status_obj, telemetry_obj)
    assert result.id == ven_id
    assert result.name == name
    assert result.status == status
    assert result.location.lat == lat
    assert result.location.lon == lon
    assert isinstance(result.createdAt, datetime)
    assert result.metrics.currentPowerKw == 1.0
    assert result.metrics.shedAvailabilityKw == 2.0
    # Check lastSeen is populated from telemetry timestamp
    assert result.lastSeen is not None
    assert isinstance(result.lastSeen, datetime)


@given(
    st.text(min_size=1, max_size=10),
    st.text(min_size=1, max_size=20),
    st.text(min_size=1, max_size=10),
    st.floats(min_value=-90, max_value=90),
    st.floats(min_value=-180, max_value=180),
    st.datetimes()
)
@settings(suppress_health_check=[HealthCheck.too_slow])
def test_build_ven_payload_no_telemetry(ven_id, name, status, lat, lon, created_at):
    """Test that lastSeen is None when telemetry is not available."""
    ven = VEN(ven_id=ven_id, name=name, status=status, latitude=lat, longitude=lon, created_at=created_at)
    status_obj = VenStatus(status=status, current_power_kw=1.0, shed_availability_kw=2.0, active_event_id=None)
    
    # Build payload without telemetry
    result = build_ven_payload(ven, status_obj, None)
    
    assert result.id == ven_id
    assert result.name == name
    assert isinstance(result.createdAt, datetime)
    # lastSeen should be None when no telemetry
    assert result.lastSeen is None


def test_build_ven_payload_includes_loads_when_requested():
    """Test that loads are included when include_loads=True."""
    from app.models.telemetry import VenLoadSample
    from datetime import UTC
    
    ven = VEN(
        ven_id="test-ven",
        name="Test VEN",
        status="online",
        latitude=37.0,
        longitude=-122.0,
        created_at=datetime.now(UTC)
    )
    
    telemetry = VenTelemetry(
        timestamp=datetime.now(UTC),
        used_power_kw=5.0,
        shed_power_kw=2.0,
        event_id=None,
        loads=[]
    )
    
    # Add mock loads to telemetry
    load1 = VenLoadSample(
        load_id="load-1",
        name="HVAC",
        type="hvac",
        capacity_kw=10.0,
        shed_capability_kw=3.0,
        current_power_kw=4.0,
    )
    load2 = VenLoadSample(
        load_id="load-2",
        name="Water Heater",
        type="water_heater",
        capacity_kw=5.0,
        shed_capability_kw=2.0,
        current_power_kw=1.0,
    )
    telemetry.loads = [load1, load2]
    
    # Test with include_loads=False (default)
    result_without_loads = build_ven_payload(ven, None, telemetry, include_loads=False)
    assert result_without_loads.loads is None
    
    # Test with include_loads=True
    result_with_loads = build_ven_payload(ven, None, telemetry, include_loads=True)
    assert result_with_loads.loads is not None
    assert len(result_with_loads.loads) == 2
    assert result_with_loads.loads[0].id == "load-1"
    assert result_with_loads.loads[0].type == "hvac"
    assert result_with_loads.loads[0].capacityKw == 10.0
    assert result_with_loads.loads[1].id == "load-2"
    assert result_with_loads.loads[1].type == "water_heater"


def test_build_ven_payload_loads_none_when_no_telemetry():
    """Test that loads are None when telemetry is not provided."""
    ven = VEN(
        ven_id="test-ven",
        name="Test VEN",
        status="online",
        latitude=37.0,
        longitude=-122.0,
        created_at=datetime.now()
    )
    
    status_obj = VenStatus(
        status="online",
        current_power_kw=1.0,
        shed_availability_kw=2.0,
        active_event_id=None
    )
    
    # Even with include_loads=True, loads should be None if no telemetry
    result = build_ven_payload(ven, status_obj, None, include_loads=True)
    assert result.loads is None
