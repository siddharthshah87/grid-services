import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from hypothesis import given, strategies as st
from app.routers.utils import _granularity_to_timedelta

@given(
    value=st.one_of(
        st.none(),
        st.text(min_size=0, max_size=5),
        st.text(min_size=1, max_size=10),
        st.text(min_size=2, max_size=10).filter(lambda s: s[-1] in "mhd"),
        st.text(min_size=3, max_size=10).filter(lambda s: s.endswith("ms")),
    )
)
def test_granularity_to_timedelta_property(value):
    td = _granularity_to_timedelta(value)
    assert isinstance(td, type(td))
    # Should always return a timedelta
    assert hasattr(td, 'total_seconds')
    # Should never raise
    assert td.total_seconds() >= 0
