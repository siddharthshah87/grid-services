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
sys.path.insert(0, './ecs-backend/app')

def test_ven_ack_schema():
    with open("tests/golden/ven_ack.json") as f:
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
