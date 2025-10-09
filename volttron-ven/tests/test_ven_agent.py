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
    module._ven_enabled = True  # Ensure enabled for publish
    # Simulate an event to trigger publish
    msg = type("M", (), {"payload": json.dumps({"ven_id": "ven1"}).encode()})()
    module.on_event(mock_client, None, msg)
    with mock.patch("time.sleep"):
        module.main(iterations=1)
    assert mock_client.publish.call_count >= 1
    mock_client.message_callback_add.assert_any_call(module.MQTT_TOPIC_EVENTS, module.on_event)
    mock_client.subscribe.assert_any_call(module.MQTT_TOPIC_EVENTS)


def test_shadow_delta_updates_interval_and_target():
    mock_client = mock.Mock()
    module = load_module(mock_client, {"IOT_THING_NAME": "demo-thing"})

    delta_msg = {"state": {"report_interval_seconds": 7, "target_power_kw": "1.5"}}
    msg = type("M", (), {"payload": json.dumps(delta_msg).encode()})()

    module.on_shadow_delta(mock_client, None, msg)

    assert module.REPORT_INTERVAL_SECONDS == 7
    assert module._shadow_target_power_kw == 1.5

    topic, payload, *_ = mock_client.publish.call_args_list[-1][0]
    assert topic == module.SHADOW_TOPIC_UPDATE
    reported = json.loads(payload)["state"]["reported"]
    assert reported["report_interval_seconds"] == 7
    assert reported["target_power_kw"] == 1.5
    assert "status" in reported and "last_shadow_delta_ts" in reported["status"]


def test_main_requests_shadow_sync_when_thing_configured():
    mock_client = mock.Mock()
    module = load_module(mock_client, {"IOT_THING_NAME": "demo-thing"})
    module._ven_enabled = True
    # Simulate a config change to trigger shadow update
    delta_msg = {"state": {"report_interval_seconds": 7, "target_power_kw": "1.5"}}
    msg = type("M", (), {"payload": json.dumps(delta_msg).encode()})()
    module.on_shadow_delta(mock_client, None, msg)
    with mock.patch("time.sleep"):
        module.main(iterations=1)
    mock_client.message_callback_add.assert_any_call(module.MQTT_TOPIC_EVENTS, module.on_event)
    mock_client.message_callback_add.assert_any_call(module.SHADOW_TOPIC_DELTA, module.on_shadow_delta)
    mock_client.subscribe.assert_any_call(module.SHADOW_TOPIC_DELTA)
    mock_client.subscribe.assert_any_call(module.SHADOW_TOPIC_GET_ACCEPTED)
    mock_client.subscribe.assert_any_call(module.SHADOW_TOPIC_GET_REJECTED)
    publish_topics = [call[0][0] for call in mock_client.publish.call_args_list]
    assert module.SHADOW_TOPIC_UPDATE in publish_topics


def test_openapi_spec_has_health():
    module = load_module(mock.Mock())
    assert "/health" in module.OPENAPI_SPEC["paths"]


def test_health_snapshot_reports_disconnected_state():
    mock_client = mock.Mock()
    module = load_module(mock_client)
    module.connected = False
    module._reconnect_in_progress = True
    module._last_disconnect_time = 0

    status, payload = module.health_snapshot()
    assert status == 200
    assert payload["ok"] is False
    assert payload["status"] == "disconnected"
    assert payload["reconnect_in_progress"] is True
    assert payload["last_disconnect_at"] == "1970-01-01T00:00:00Z"
    assert "last_connected_at" not in payload


def test_health_snapshot_reports_connected_state():
    mock_client = mock.Mock()
    module = load_module(mock_client)
    module.connected = True
    module._reconnect_in_progress = False
    module._last_connect_time = 0
    module._last_publish_time = 0

    status, payload = module.health_snapshot()
    assert status == 200
    assert payload["ok"] is True
    assert payload["status"] == "connected"
    assert payload["manual_tls_hostname_override"] is False
    assert payload["last_connected_at"] == "1970-01-01T00:00:00Z"
    assert payload["last_publish_at"] == "1970-01-01T00:00:00Z"
    assert payload["detail"].startswith("MQTT connection established")


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
    mock_client.reconnect_delay_set.assert_called_once_with(min_delay=1, max_delay=60)
    mock_client.tls_insecure_set.assert_called_with(True)
    mock_client.connect.assert_any_call(
        "vpce-test.iot.internal", module.MQTT_PORT, 60
    )
    module.client.on_connect(mock_client, None, None, 0)
    mock_client.socket.assert_called_once()
    mock_socket.getpeercert.assert_called_once()
    mock_client.disconnect.assert_not_called()
