import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from hypothesis import given, strategies as st
from app.data.dummy import set_event, get_event
from app.schemas.api_models import Event
from datetime import datetime

@given(
    st.text(min_size=1, max_size=10),
    st.text(min_size=1, max_size=10),
    st.datetimes(),
    st.datetimes(),
    st.one_of(st.none(), st.floats(min_value=0, max_value=1000)),
    st.floats(min_value=0, max_value=1000)
)
def test_set_and_get_event(event_id, status, start, end, requested_reduction, actual_reduction):
    evt = Event(
        id=event_id,
        status=status,
        startTime=start,
        endTime=end,
        requestedReductionKw=requested_reduction,
        actualReductionKw=actual_reduction
    )
    set_event(evt)
    fetched = get_event(event_id)
    assert fetched is not None
    assert fetched.id == event_id
    assert fetched.status == status
    assert fetched.startTime == start
    assert fetched.endTime == end
    assert fetched.requestedReductionKw == requested_reduction
    assert fetched.actualReductionKw == actual_reduction
