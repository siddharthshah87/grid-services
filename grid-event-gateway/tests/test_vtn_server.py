import json
import os
import importlib.util
from pathlib import Path
from unittest import mock
import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "vtn_server.py"


def load_module(mock_client, env_overrides=None):
    env = {
        "CERT_BUNDLE_JSON": json.dumps({
            "ca.crt": "CA",
            "client.crt": "CLIENT",
            "private.key": "KEY"
        }),
        # Use an ephemeral port for the VEN listing server so multiple test
        # runs don't conflict over the same port.
        "VENS_PORT": "0",
    }
    if env_overrides:
        env.update(env_overrides)
    with mock.patch.dict(os.environ, env, clear=False), \
            mock.patch("paho.mqtt.client.Client", return_value=mock_client):
        spec = importlib.util.spec_from_file_location("vtn_server", MODULE_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


def test_write_temp_file(tmp_path):
    module = load_module(mock.Mock())
    path = module.write_temp_file("data", ".crt")
    assert Path(path).read_text() == "data"
    os.remove(path)
    with pytest.raises(ValueError):
        module.write_temp_file("", ".crt")


def test_handle_event_request_publishes():
    mock_client = mock.Mock()
    module = load_module(mock_client)
    result = module.handle_event_request("ven1", {})
    mock_client.publish.assert_called_once()
    topic, payload = mock_client.publish.call_args[0]
    assert topic == module.MQTT_TOPIC_EVENTS
    data = json.loads(payload)
    assert data["ven_id"] == "ven1"
    assert result[0]["targets"]["ven_id"] == "ven1"


def test_openapi_spec_has_health():
    module = load_module(mock.Mock())
    assert "/health" in module.OPENAPI_SPEC["paths"]


def test_tls_hostname_override_enables_manual_check():
    mock_client = mock.Mock()
    mock_socket = mock.Mock()
    mock_socket.getpeercert.return_value = {
        "subject": ((("commonName", "va1mgxpe8mg484j-ats.iot.us-west-2.amazonaws.com"),),),
        "subjectAltName": (("DNS", "va1mgxpe8mg484j-ats.iot.us-west-2.amazonaws.com"),),
    }
    mock_client.socket.return_value = mock_socket

    module = load_module(mock_client, {
        "IOT_CONNECT_HOST": "vpce-test.iot.internal",
        "IOT_TLS_SERVER_NAME": "va1mgxpe8mg484j-ats.iot.us-west-2.amazonaws.com",
    })

    assert module.manual_hostname_override is True
    mock_client.tls_insecure_set.assert_called_with(True)
    mock_client.connect.assert_called_once_with(
        "vpce-test.iot.internal", module.MQTT_PORT, keepalive=60
    )
    mock_client.socket.assert_called_once()
    mock_socket.getpeercert.assert_called_once()
    mock_client.disconnect.assert_not_called()

