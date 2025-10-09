import json
import sys
sys.path.insert(0, './ecs-backend/app')
from schemas.api_models import Ven

def test_ven_payload_schema():
    with open("tests/golden/ven_payload.json") as f:
        payload = json.load(f)
    ven = Ven(**payload)  # Should not raise
    assert ven.id
    assert ven.metrics.currentPowerKw >= 0
    assert ven.location.lat and ven.location.lon
    assert isinstance(ven.loads, list)
    for load in ven.loads:
        assert "id" in load.dict()
        assert "currentPowerKw" in load.dict()
