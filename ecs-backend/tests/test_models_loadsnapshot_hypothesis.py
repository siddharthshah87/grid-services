import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from hypothesis import given, strategies as st
from datetime import datetime
from app.models.telemetry import LoadSnapshot

@given(
    ven_id=st.text(min_size=1, max_size=20),
    timestamp=st.datetimes(),
    load_id=st.text(min_size=1, max_size=20),
    name=st.one_of(st.none(), st.text(max_size=50)),
    type=st.one_of(st.none(), st.text(max_size=50)),
    capacity_kw=st.one_of(st.none(), st.floats(min_value=0, max_value=10000)),
    current_power_kw=st.one_of(st.none(), st.floats(min_value=0, max_value=10000)),
    shed_capability_kw=st.one_of(st.none(), st.floats(min_value=0, max_value=10000)),
    enabled=st.one_of(st.none(), st.booleans()),
    priority=st.one_of(st.none(), st.integers(min_value=0, max_value=100)),
    raw_payload=st.one_of(st.none(), st.dictionaries(st.text(max_size=10), st.integers())),
    created_at=st.datetimes()
)
def test_loadsnapshot_model_property(
    ven_id,
    timestamp,
    load_id,
    name,
    type,
    capacity_kw,
    current_power_kw,
    shed_capability_kw,
    enabled,
    priority,
    raw_payload,
    created_at
):
    obj = LoadSnapshot(
        ven_id=ven_id,
        timestamp=timestamp,
        load_id=load_id,
        name=name,
        type=type,
        capacity_kw=capacity_kw,
        current_power_kw=current_power_kw,
        shed_capability_kw=shed_capability_kw,
        enabled=enabled,
        priority=priority,
        raw_payload=raw_payload,
        created_at=created_at
    )
    assert obj.ven_id == ven_id
    assert obj.timestamp == timestamp
    assert obj.load_id == load_id
    assert obj.name == name
    assert obj.type == type
    assert obj.capacity_kw == capacity_kw
    assert obj.current_power_kw == current_power_kw
    assert obj.shed_capability_kw == shed_capability_kw
    assert obj.enabled == enabled
    assert obj.priority == priority
    assert obj.raw_payload == raw_payload
    assert obj.created_at == created_at
