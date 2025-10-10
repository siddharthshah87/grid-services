import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from hypothesis import given, strategies as st
from app.data.dummy import get_load_type_stats, upsert_ven
from app.schemas.api_models import Load
from datetime import datetime

@given(
    st.text(min_size=1, max_size=10),
    st.text(min_size=1, max_size=10),
    st.floats(min_value=0, max_value=1000),
    st.floats(min_value=0, max_value=1000),
    st.floats(min_value=0, max_value=1000)
)
def test_get_load_type_stats_property(id, type_, capacity, shed, current):
    # Create a dummy VEN with one load
    from app.schemas.api_models import Ven, Location, VenMetrics
    ven = Ven(
        id=id,
        name="Test",
        status="online",
        location=Location(lat=0.0, lon=0.0),
        metrics=VenMetrics(currentPowerKw=current, shedAvailabilityKw=shed, activeEventId=None, shedLoadIds=[]),
        createdAt=datetime.utcnow(),
        loads=[Load(id=id, type=type_, capacityKw=capacity, shedCapabilityKw=shed, currentPowerKw=current, name=None)]
    )
    upsert_ven(ven)
    stats = get_load_type_stats()
    # Should return at least one entry for the type
    assert any(s.type == type_ for s in stats)
    # All stats should have non-negative values
    for s in stats:
        assert s.totalCapacityKw >= 0
        assert s.totalShedCapabilityKw >= 0
        assert s.currentUsageKw >= 0
