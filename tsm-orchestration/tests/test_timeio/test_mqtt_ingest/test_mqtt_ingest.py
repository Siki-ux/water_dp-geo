import json
import pytest
from unittest.mock import MagicMock, patch
from paho.mqtt.client import MQTTMessage
from run_mqtt_ingest import ParseMqttDataHandler


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("TOPIC", "test/topic")
    monkeypatch.setenv("MQTT_BROKER", "broker:1883")
    monkeypatch.setenv("MQTT_USER", "user")
    monkeypatch.setenv("MQTT_PASSWORD", "pw")
    monkeypatch.setenv("MQTT_CLIENT_ID", "cid")
    monkeypatch.setenv("MQTT_QOS", "1")
    monkeypatch.setenv("MQTT_CLEAN_SESSION", "true")
    monkeypatch.setenv("CONFIGDB_DSN", "dsn")
    monkeypatch.setenv("DB_API_BASE_URL", "http://fake-db")
    monkeypatch.setenv("TOPIC_DATA_PARSED", "topic/parsed")


@patch("run_mqtt_ingest.DBapi")
@patch("run_mqtt_ingest.Thing")
@patch("run_mqtt_ingest.get_parser")
def test_act_parses_and_publishes(mock_get_parser, mock_Thing, mock_DBapi, mock_env):
    handler = ParseMqttDataHandler()
    msg = MQTTMessage(topic=b"user/topic")
    msg.payload = b"{}"

    mock_thing = MagicMock()
    mock_thing.uuid = "UUID"
    mock_thing.mqtt.mqtt_device_type.name = "campbell_cr6"
    mock_Thing.from_mqtt_user_name.return_value = mock_thing

    parser_instance = MagicMock()
    parser_instance.do_parse.return_value = ["parsed"]
    parser_instance.to_observations.return_value = [{"result_number": 1}]
    mock_get_parser.return_value = parser_instance

    handler.dbapi.upsert_observations = MagicMock()
    handler.mqtt_client = MagicMock()

    handler.act({}, msg)

    handler.dbapi.upsert_observations.assert_called_once_with(
        "UUID", [{"result_number": 1}]
    )
    handler.mqtt_client.publish.assert_called_once()
    args, kwargs = handler.mqtt_client.publish.call_args
    assert handler.pub_topic in kwargs["topic"] or args[0] == handler.pub_topic
    payload = json.loads(kwargs.get("payload") or args[1])
    assert payload["thing_uuid"] == "UUID"
