import pytest
from hypothesis import given, strategies as st
from datetime import datetime
from app.models.telemetry import VenLoadSample

@given(
    telemetry_id=st.integers(min_value=1, max_value=10000),
    load_id=st.text(min_size=1, max_size=20),
    name=st.one_of(st.none(), st.text(max_size=50)),
    type=st.one_of(st.none(), st.text(max_size=50)),
    capacity_kw=st.one_of(st.none(), st.floats(allow_nan=False, allow_infinity=False, min_value=0, max_value=10000)),
    current_power_kw=st.one_of(st.none(), st.floats(allow_nan=False, allow_infinity=False, min_value=0, max_value=10000)),
    shed_capability_kw=st.one_of(st.none(), st.floats(allow_nan=False, allow_infinity=False, min_value=0, max_value=10000)),
    enabled=st.one_of(st.none(), st.booleans()),
    priority=st.one_of(st.none(), st.integers(min_value=0, max_value=100)),
    raw_payload=st.one_of(st.none(), st.dictionaries(st.text(max_size=10), st.integers())),
)
def test_ven_load_sample_fields(
    telemetry_id,
    load_id,
    name,
    type,
    capacity_kw,
    current_power_kw,
    shed_capability_kw,
    enabled,
    priority,
    raw_payload,
):
    obj = VenLoadSample(
        telemetry_id=telemetry_id,
        load_id=load_id,
        name=name,
        type=type,
        capacity_kw=capacity_kw,
        current_power_kw=current_power_kw,
        shed_capability_kw=shed_capability_kw,
        enabled=enabled,
        priority=priority,
        raw_payload=raw_payload,
    )
    assert obj.telemetry_id == telemetry_id
    assert obj.load_id == load_id
    assert obj.name == name
    assert obj.type == type
    assert obj.capacity_kw == capacity_kw
    assert obj.current_power_kw == current_power_kw
    assert obj.shed_capability_kw == shed_capability_kw
    assert obj.enabled == enabled
    assert obj.priority == priority
    assert obj.raw_payload == raw_payload
