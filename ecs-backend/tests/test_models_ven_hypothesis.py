import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from hypothesis import given, strategies as st
from app.models.ven import VEN
from datetime import datetime

@given(
    st.text(min_size=1, max_size=10),
    st.one_of(st.none(), st.text(min_size=1, max_size=10)),
    st.text(min_size=1, max_size=20),
    st.text(min_size=1, max_size=10),
    st.one_of(st.none(), st.floats(min_value=-90, max_value=90)),
    st.one_of(st.none(), st.floats(min_value=-180, max_value=180)),
    st.datetimes()
)
def test_ven_model_sqlalchemy_property(ven_id, registration_id, name, status, latitude, longitude, created_at):
    ven = VEN(
        ven_id=ven_id,
        registration_id=registration_id,
        name=name,
        status=status,
        latitude=latitude,
        longitude=longitude,
        created_at=created_at
    )
    assert ven.ven_id == ven_id
    assert ven.registration_id == registration_id
    assert ven.name == name
    assert ven.status == status
    assert ven.latitude == latitude
    assert ven.longitude == longitude
    assert ven.created_at == created_at
