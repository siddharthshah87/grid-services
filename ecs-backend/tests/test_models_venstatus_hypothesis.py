import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from hypothesis import given, strategies as st
from datetime import datetime
from app.models.telemetry import VenStatus

@given(
    ven_id=st.text(min_size=1, max_size=20),
    timestamp=st.datetimes(),
    status=st.text(min_size=1, max_size=10),
    current_power_kw=st.one_of(st.none(), st.floats(min_value=-10000, max_value=10000)),
    shed_availability_kw=st.one_of(st.none(), st.floats(min_value=0, max_value=10000)),
    active_event_id=st.one_of(st.none(), st.text(min_size=1, max_size=20)),
    raw_payload=st.one_of(st.none(), st.dictionaries(st.text(max_size=10), st.integers())),
    created_at=st.datetimes()
)
def test_venstatus_model_property(
    ven_id,
    timestamp,
    status,
    current_power_kw,
    shed_availability_kw,
    active_event_id,
    raw_payload,
    created_at
):
    obj = VenStatus(
        ven_id=ven_id,
        timestamp=timestamp,
        status=status,
        current_power_kw=current_power_kw,
        shed_availability_kw=shed_availability_kw,
        active_event_id=active_event_id,
        raw_payload=raw_payload,
        created_at=created_at
    )
    assert obj.ven_id == ven_id
    assert obj.timestamp == timestamp
    assert obj.status == status
    assert obj.current_power_kw == current_power_kw
    assert obj.shed_availability_kw == shed_availability_kw
    assert obj.active_event_id == active_event_id
    assert obj.raw_payload == raw_payload
    assert obj.created_at == created_at
