import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from hypothesis import given, strategies as st
from app.data.dummy import set_event, event_metrics
from app.schemas.api_models import Event, EventMetrics
from datetime import datetime

@given(
    st.text(min_size=1, max_size=10),
    st.text(min_size=1, max_size=10),
    st.datetimes(),
    st.datetimes(),
    st.floats(min_value=0, max_value=1000),
    st.floats(min_value=0, max_value=1000)
)
def test_event_metrics_property(event_id, status, start, end, requested_reduction, actual_reduction):
    evt = Event(
        id=event_id,
        status=status,
        startTime=start,
        endTime=end,
        requestedReductionKw=requested_reduction,
        actualReductionKw=actual_reduction
    )
    set_event(evt)
    metrics = event_metrics(event_id)
    if metrics is not None:
        assert isinstance(metrics, EventMetrics)
        # Should be 40% of requestedReductionKw
        assert metrics.currentReductionKw == round(requested_reduction * 0.4, 2)
        assert metrics.vensResponding == 238
        assert metrics.avgResponseMs == 142
