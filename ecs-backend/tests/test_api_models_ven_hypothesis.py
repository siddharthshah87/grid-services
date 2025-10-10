import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from hypothesis import given, strategies as st
from datetime import datetime
from app.schemas.api_models import Ven, Location, VenMetrics, Load

@given(
    st.text(min_size=1, max_size=10),  # id
    st.text(min_size=1, max_size=20),  # name
    st.text(min_size=1, max_size=10),  # status
    st.floats(min_value=-90, max_value=90),  # lat
    st.floats(min_value=-180, max_value=180),  # lon
    st.floats(min_value=0, max_value=10000),  # currentPowerKw
    st.floats(min_value=0, max_value=10000),  # shedAvailabilityKw
    st.one_of(st.none(), st.text(min_size=0, max_size=20)),  # activeEventId
    st.lists(st.text(min_size=1, max_size=10), max_size=10),  # shedLoadIds
    st.datetimes(),  # createdAt
    st.lists(
        st.builds(
            Load,
            id=st.text(min_size=1, max_size=10),
            type=st.text(min_size=1, max_size=10),
            capacityKw=st.floats(min_value=0, max_value=1000),
            shedCapabilityKw=st.floats(min_value=0, max_value=1000),
            currentPowerKw=st.floats(min_value=0, max_value=1000),
            name=st.one_of(st.none(), st.text(min_size=0, max_size=20))
        ), max_size=5
    )
)
def test_ven_model_property(
    ven_id, name, status, lat, lon, current, shed, event_id, shed_load_ids, created_at, loads
):
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
        loads=loads
    )
    assert isinstance(ven.id, str)
    assert isinstance(ven.name, str)
    assert isinstance(ven.status, str)
    assert isinstance(ven.location, Location)
    assert isinstance(ven.metrics, VenMetrics)
    assert isinstance(ven.createdAt, datetime)
    assert ven.loads is None or all(isinstance(l, Load) for l in ven.loads)
    d = ven.dict()
    assert d["id"] == ven_id
    assert d["name"] == name
    assert d["status"] == status
    assert d["location"]["lat"] == lat
    assert d["location"]["lon"] == lon
    assert d["metrics"]["currentPowerKw"] == current
    assert d["metrics"]["shedAvailabilityKw"] == shed
    assert d["metrics"]["activeEventId"] == event_id
    assert d["metrics"]["shedLoadIds"] == shed_load_ids
    assert d["createdAt"] == created_at
    if ven.loads is not None:
        for i, l in enumerate(ven.loads):
            assert d["loads"][i]["id"] == l.id
