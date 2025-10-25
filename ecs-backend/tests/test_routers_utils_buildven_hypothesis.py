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
