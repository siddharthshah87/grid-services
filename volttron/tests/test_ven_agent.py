import importlib.util
from pathlib import Path
from unittest import mock
import os
import json

MODULE_PATH = Path(__file__).resolve().parents[1] / "ven_agent.py"


def load_module(mock_client):
    env = {"HEALTH_PORT": "0"}
    with mock.patch.dict(os.environ, env, clear=False), \
            mock.patch("paho.mqtt.client.Client", return_value=mock_client):
        spec = importlib.util.spec_from_file_location("ven_agent", MODULE_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


def test_on_event_publishes_response():
    mock_client = mock.Mock()
    module = load_module(mock_client)
    msg = type("M", (), {"payload": json.dumps({"ven_id": "ven1"}).encode()})()
    module.on_event(mock_client, None, msg)
    mock_client.publish.assert_called_once()
    topic, payload = mock_client.publish.call_args[0]
    assert topic == module.MQTT_TOPIC_RESPONSES
    assert json.loads(payload)["ven_id"] == "ven1"


def test_main_one_iteration():
    mock_client = mock.Mock()
    module = load_module(mock_client)
    with mock.patch("time.sleep"):
        module.main(iterations=1)
    assert mock_client.publish.call_count >= 2


def test_openapi_spec_has_health():
    module = load_module(mock.Mock())
    assert "/health" in module.OPENAPI_SPEC["paths"]



