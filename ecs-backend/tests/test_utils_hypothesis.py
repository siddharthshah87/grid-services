
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from hypothesis import given, strategies as st
from app.routers.utils import _granularity_to_timedelta
from datetime import timedelta

@given(st.one_of(st.none(), st.text(min_size=0, max_size=8)))
def test_granularity_to_timedelta_property(value):
    td = _granularity_to_timedelta(value)
    # Should always return a timedelta
    assert isinstance(td, timedelta)
    # Should never raise
    # For known units, check expected bounds
    if value is None or value.strip() == "":
        assert td == timedelta(minutes=5)
    elif value.endswith("ms"):
        try:
            amount = int(value[:-2])
            assert td == timedelta(milliseconds=amount)
        except Exception:
            assert td == timedelta(minutes=5)
    elif value[-1] in "mhd":
        try:
            amount = int(value[:-1])
            if value[-1] == "m":
                assert td == timedelta(minutes=amount)
            elif value[-1] == "h":
                assert td == timedelta(hours=amount)
            elif value[-1] == "d":
                assert td == timedelta(days=amount)
        except Exception:
            assert td == timedelta(minutes=5)
    else:
        assert td == timedelta(minutes=5)
