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
