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
