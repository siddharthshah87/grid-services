from hypothesis import given, strategies as st
@given(
    st.fixed_dictionaries({
        "op": st.just("shedLoad"),
        "correlationId": st.text(min_size=1, max_size=20),
        "venId": st.text(min_size=1, max_size=20),
        "data": st.fixed_dictionaries({"amountKw": st.floats(min_value=0, max_value=10000)})
    })
)
def test_backend_cmd_property(payload):
    required = ["op", "correlationId", "venId", "data"]
    for field in required:
        assert field in payload
    assert payload["op"] == "shedLoad"
    assert isinstance(payload["venId"], str)
    assert "amountKw" in payload["data"]
import json

def test_backend_cmd_schema():
    with open("tests/golden/backend_cmd.json") as f:
        payload = json.load(f)
    required = ["op", "correlationId", "venId", "data"]
    for field in required:
        assert field in payload
    assert payload["op"] == "shedLoad"
    assert isinstance(payload["venId"], str)
    assert "amountKw" in payload["data"]
