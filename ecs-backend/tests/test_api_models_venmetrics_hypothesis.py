import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from hypothesis import given, strategies as st
from app.schemas.api_models import VenMetrics

@given(
    st.floats(min_value=0, max_value=10000),
    st.floats(min_value=0, max_value=10000),
    st.one_of(st.none(), st.text(min_size=0, max_size=20)),
    st.lists(st.text(min_size=1, max_size=10), max_size=10)
)
def test_venmetrics_model_property(current, shed, event_id, shed_load_ids):
    metrics = VenMetrics(currentPowerKw=current, shedAvailabilityKw=shed, activeEventId=event_id, shedLoadIds=shed_load_ids)
    assert isinstance(metrics.currentPowerKw, float)
    assert isinstance(metrics.shedAvailabilityKw, float)
    assert metrics.activeEventId is None or isinstance(metrics.activeEventId, str)
    assert isinstance(metrics.shedLoadIds, list)
    for load_id in metrics.shedLoadIds:
        assert isinstance(load_id, str)
    d = metrics.dict()
    assert d["currentPowerKw"] == current
    assert d["shedAvailabilityKw"] == shed
    assert d["activeEventId"] == event_id
    assert d["shedLoadIds"] == shed_load_ids
