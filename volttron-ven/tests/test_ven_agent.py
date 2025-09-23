import importlib.util
import json
import os
from pathlib import Path
from unittest import mock

MODULE_PATH = Path(__file__).resolve().parents[1] / "ven_agent.py"


FAKE_CERT = """-----BEGIN CERTIFICATE-----\nfake\n-----END CERTIFICATE-----"""
FAKE_KEY = """-----BEGIN PRIVATE KEY-----\nfake\n-----END PRIVATE KEY-----"""


def load_module(mock_client, env_overrides=None):
    env = {
        "HEALTH_PORT": "0",
        "CA_CERT_PEM": FAKE_CERT,
        "CLIENT_CERT_PEM": FAKE_CERT,
        "PRIVATE_KEY_PEM": FAKE_KEY,
        "TLS_SECRET_NAME": "",
    }
    if env_overrides:
        env.update(env_overrides)
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
        "vpce-test.iot.internal", module.MQTT_PORT, 60
    )
    mock_client.socket.assert_called_once()
    mock_socket.getpeercert.assert_called_once()
    mock_client.disconnect.assert_not_called()

