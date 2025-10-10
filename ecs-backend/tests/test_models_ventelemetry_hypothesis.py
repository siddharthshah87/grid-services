import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from hypothesis import given, strategies as st
from app.models.telemetry import VenTelemetry
from datetime import datetime

@given(
    st.integers(min_value=1, max_value=10000),
    st.text(min_size=1, max_size=10),
    st.datetimes(),
    st.one_of(st.none(), st.floats(min_value=0, max_value=10000)),
    st.one_of(st.none(), st.floats(min_value=0, max_value=10000)),
    st.one_of(st.none(), st.floats(min_value=0, max_value=10000)),
    st.one_of(st.none(), st.text(min_size=1, max_size=10)),
    st.one_of(st.none(), st.floats(min_value=0, max_value=100)),
    st.one_of(st.none(), st.dictionaries(st.text(min_size=1, max_size=5), st.floats(min_value=0, max_value=100))),
    st.datetimes()
)
def test_ventelemetry_model_sqlalchemy_property(id, ven_id, timestamp, used_power, shed_power, requested_reduction, event_id, battery_soc, raw_payload, created_at):
    telemetry = VenTelemetry(
        id=id,
        ven_id=ven_id,
        timestamp=timestamp,
        used_power_kw=used_power,
        shed_power_kw=shed_power,
        requested_reduction_kw=requested_reduction,
        event_id=event_id,
        battery_soc=battery_soc,
        raw_payload=raw_payload,
        created_at=created_at
    )
    assert telemetry.id == id
    assert telemetry.ven_id == ven_id
    assert telemetry.timestamp == timestamp
    assert telemetry.used_power_kw == used_power
    assert telemetry.shed_power_kw == shed_power
    assert telemetry.requested_reduction_kw == requested_reduction
    assert telemetry.event_id == event_id
    assert telemetry.battery_soc == battery_soc
    assert telemetry.raw_payload == raw_payload
    assert telemetry.created_at == created_at
