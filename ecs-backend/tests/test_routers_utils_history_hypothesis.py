import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from hypothesis import given, strategies as st
from app.routers.utils import build_history_response
from app.models.telemetry import VenTelemetry
from datetime import datetime, timezone

@given(
    st.lists(
        st.builds(
            VenTelemetry,
            timestamp=st.datetimes(),
            used_power_kw=st.floats(min_value=0, max_value=1000),
            shed_power_kw=st.floats(min_value=0, max_value=1000),
            requested_reduction_kw=st.one_of(st.none(), st.floats(min_value=0, max_value=1000)),
            event_id=st.one_of(st.none(), st.text(min_size=1, max_size=10)),
            loads=st.just([])
        ), max_size=10
    ),
    st.one_of(st.none(), st.text(min_size=1, max_size=5))
)
def test_build_history_response_property(telemetries, granularity):
    result = build_history_response(telemetries, granularity)
    # Should always return a HistoryResponse
    assert hasattr(result, "points")
    # All points should have required fields
    for pt in result.points:
        assert hasattr(pt, "timestamp")
        assert hasattr(pt, "usedPowerKw")
        assert hasattr(pt, "shedPowerKw")
