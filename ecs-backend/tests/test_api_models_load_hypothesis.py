import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from hypothesis import given, strategies as st
from app.schemas.api_models import Load

@given(
    st.text(min_size=1, max_size=10),
    st.text(min_size=1, max_size=10),
    st.floats(min_value=0, max_value=1000),
    st.floats(min_value=0, max_value=1000),
    st.floats(min_value=0, max_value=1000),
    st.one_of(st.none(), st.text(min_size=0, max_size=20))
)
def test_load_model_property(id, type_, capacity, shed, current, name):
    load = Load(id=id, type=type_, capacityKw=capacity, shedCapabilityKw=shed, currentPowerKw=current, name=name)
    assert isinstance(load.id, str)
    assert isinstance(load.type, str)
    assert isinstance(load.capacityKw, float)
    assert isinstance(load.shedCapabilityKw, float)
    assert isinstance(load.currentPowerKw, float)
    # Name can be None or str
    assert load.name is None or isinstance(load.name, str)
    d = load.dict()
    assert d["id"] == id
    assert d["type"] == type_
    assert d["capacityKw"] == capacity
    assert d["shedCapabilityKw"] == shed
    assert d["currentPowerKw"] == current
    assert d["name"] == name
