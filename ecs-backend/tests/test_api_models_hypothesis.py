import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from hypothesis import given, strategies as st
from app.schemas.api_models import Location

@given(st.floats(min_value=-90, max_value=90), st.floats(min_value=-180, max_value=180))
def test_location_model_property(lat, lon):
    loc = Location(lat=lat, lon=lon)
    # Should always have correct types
    assert isinstance(loc.lat, float)
    assert isinstance(loc.lon, float)
    # Should serialize to dict with correct values
    d = loc.dict()
    assert d["lat"] == lat
    assert d["lon"] == lon
