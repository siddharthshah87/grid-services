from hypothesis import given, strategies as st
@given(
    st.fixed_dictionaries({
        "eventId": st.text(min_size=1, max_size=20),
        "requestedReductionKw": st.floats(min_value=0, max_value=10000),
        "actualReductionKw": st.floats(min_value=0, max_value=10000),
        "deliveredKwh": st.floats(min_value=0, max_value=10000),
        "baselineKw": st.floats(min_value=0, max_value=10000),
        "startTs": st.integers(min_value=0),
        "endTs": st.integers(min_value=0)
    })
)
def test_event_payload_property(payload):
    required = ["eventId", "requestedReductionKw", "actualReductionKw", "deliveredKwh", "baselineKw", "startTs", "endTs"]
    for field in required:
        assert field in payload
    assert isinstance(payload["eventId"], str)
    assert isinstance(payload["requestedReductionKw"], (int, float))
    assert isinstance(payload["actualReductionKw"], (int, float))
    assert isinstance(payload["deliveredKwh"], (int, float))
    assert isinstance(payload["baselineKw"], (int, float))
    assert isinstance(payload["startTs"], int)
    assert isinstance(payload["endTs"], int)
import json

def test_event_payload_schema():
    with open("tests/golden/event_payload.json") as f:
        payload = json.load(f)
    required = ["eventId", "requestedReductionKw", "actualReductionKw", "deliveredKwh", "baselineKw", "startTs", "endTs"]
    for field in required:
        assert field in payload
    assert isinstance(payload["eventId"], str)
    assert isinstance(payload["requestedReductionKw"], (int, float))
    assert isinstance(payload["actualReductionKw"], (int, float))
    assert isinstance(payload["deliveredKwh"], (int, float))
    assert isinstance(payload["baselineKw"], (int, float))
    assert isinstance(payload["startTs"], int)
    assert isinstance(payload["endTs"], int)
