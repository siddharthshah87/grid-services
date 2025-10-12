from hypothesis import given, strategies as st
@given(
    st.fixed_dictionaries({
        "op": st.just("shedLoad"),
        "correlationId": st.text(min_size=1, max_size=20),
        "ok": st.booleans(),
        "ts": st.integers(min_value=0),
        "venId": st.text(min_size=1, max_size=20),
        "data": st.fixed_dictionaries({"shedAmount": st.floats(min_value=0, max_value=10000)})
    })
)
def test_ven_ack_property(payload):
    required = ["op", "correlationId", "ok", "ts", "venId", "data"]
    for field in required:
        assert field in payload
    assert payload["op"] == "shedLoad"
    assert isinstance(payload["ok"], bool)
    assert isinstance(payload["ts"], int)
    assert isinstance(payload["venId"], str)
    assert "shedAmount" in payload["data"]
import json
import sys
import os
# Add the ecs-backend app directory to sys.path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ecs-backend', 'app'))

def test_ven_ack_schema():
    import os
    golden_path = os.path.join(os.path.dirname(__file__), "golden", "ven_ack.json")
    with open(golden_path) as f:
        payload = json.load(f)
    # Minimal schema check
    required = ["op", "correlationId", "ok", "ts", "venId", "data"]
    for field in required:
        assert field in payload
    assert payload["op"] == "shedLoad"
    assert isinstance(payload["ok"], bool)
    assert isinstance(payload["ts"], int)
    assert isinstance(payload["venId"], str)
    assert "shedAmount" in payload["data"]
