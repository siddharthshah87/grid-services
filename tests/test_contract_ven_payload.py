from hypothesis import given, strategies as st
from datetime import datetime
@given(
    st.fixed_dictionaries({
        "id": st.text(min_size=1, max_size=20),
        "name": st.text(min_size=1, max_size=50),
        "status": st.sampled_from(["active", "inactive", "error"]),
        "location": st.fixed_dictionaries({
            "lat": st.floats(min_value=-90, max_value=90),
            "lon": st.floats(min_value=-180, max_value=180),
        }),
        "metrics": st.fixed_dictionaries({
            "currentPowerKw": st.floats(min_value=0, max_value=10000),
            "shedAvailabilityKw": st.floats(min_value=0, max_value=10000),
            "activeEventId": st.text(min_size=0, max_size=20),
            "shedLoadIds": st.lists(st.text(min_size=1, max_size=10), max_size=10),
        }),
        "createdAt": st.just(datetime.utcnow().isoformat()),
        "loads": st.lists(
            st.fixed_dictionaries({
                "id": st.text(min_size=1, max_size=10),
                "type": st.text(min_size=1, max_size=10),
                "capacityKw": st.floats(min_value=0, max_value=10000),
                "shedCapabilityKw": st.floats(min_value=0, max_value=10000),
                "currentPowerKw": st.floats(min_value=0, max_value=10000),
                "name": st.text(min_size=0, max_size=20),
            }), max_size=10
        ),
    })
)
def test_ven_payload_property(payload):
    # Should not raise for valid random payloads
    ven = Ven(**payload)
    assert ven.id
    assert isinstance(ven.loads, list)
import json
import sys
import os
# Add the ecs-backend app directory to sys.path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ecs-backend', 'app'))
from schemas.api_models import Ven

import pytest

def load_payload(path):
    import os
    golden_path = os.path.join(os.path.dirname(__file__), "golden", path)
    with open(golden_path) as f:
        return json.load(f)

def test_ven_payload_schema():
    payload = load_payload("ven_payload.json")
    ven = Ven(**payload)
    assert ven.id
    assert ven.metrics.currentPowerKw >= 0
    assert ven.location.lat and ven.location.lon
    assert isinstance(ven.loads, list)
    for load in ven.loads:
        assert "id" in load.model_dump()
        assert "currentPowerKw" in load.model_dump()

def test_ven_payload_missing_field():
    payload = load_payload("ven_payload.json")
    del payload["id"]
    with pytest.raises(Exception):
        Ven(**payload)

def test_ven_payload_invalid_type():
    payload = load_payload("ven_payload.json")
    payload["metrics"]["currentPowerKw"] = "not-a-number"
    with pytest.raises(Exception):
        Ven(**payload)

def test_ven_payload_large_loads():
    payload = load_payload("ven_payload.json")
    payload["loads"] = [payload["loads"][0]] * 1000
    ven = Ven(**payload)
    assert len(ven.loads) == 1000
