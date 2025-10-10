import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from hypothesis import given, strategies as st
from app.core.config import _unique

@given(st.lists(st.one_of(st.none(), st.text(min_size=0, max_size=10)), max_size=20))
def test_unique_property(input_list):
    result = _unique(input_list)
    # All elements in result are non-empty strings
    assert all(isinstance(x, str) and x for x in result)
    # Result preserves order of first occurrence
    seen = set()
    expected = []
    for v in input_list:
        if v and v not in seen:
            seen.add(v)
            expected.append(v)
    assert result == expected
    # Result contains only unique values
    assert len(result) == len(set(result))
