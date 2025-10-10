import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from hypothesis import given, strategies as st
from app.data.dummy import upsert_ven, get_ven
from app.schemas.api_models import Ven, Location, VenMetrics
from datetime import datetime

@given(
    st.text(min_size=1, max_size=10),
    st.text(min_size=1, max_size=20),
    st.text(min_size=1, max_size=10),
    st.floats(min_value=-90, max_value=90),
    st.floats(min_value=-180, max_value=180),
    st.floats(min_value=0, max_value=10000),
    st.floats(min_value=0, max_value=10000),
    st.one_of(st.none(), st.text(min_size=0, max_size=20)),
    st.lists(st.text(min_size=1, max_size=10), max_size=10),
    st.datetimes()
)
def test_upsert_and_get_ven(ven_id, name, status, lat, lon, current, shed, event_id, shed_load_ids, created_at):
    location = Location(lat=lat, lon=lon)
    metrics = VenMetrics(
        currentPowerKw=current,
        shedAvailabilityKw=shed,
        activeEventId=event_id,
        shedLoadIds=shed_load_ids
    )
    ven = Ven(
        id=ven_id,
        name=name,
        status=status,
        location=location,
        metrics=metrics,
        createdAt=created_at,
        loads=None
    )
    upsert_ven(ven)
    fetched = get_ven(ven_id)
    assert fetched is not None
    assert fetched.id == ven_id
    assert fetched.name == name
    assert fetched.status == status
    assert fetched.location.lat == lat
    assert fetched.location.lon == lon
    assert fetched.metrics.currentPowerKw == current
    assert fetched.metrics.shedAvailabilityKw == shed
    assert fetched.metrics.activeEventId == event_id
    assert fetched.metrics.shedLoadIds == shed_load_ids
    assert fetched.createdAt == created_at
