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
