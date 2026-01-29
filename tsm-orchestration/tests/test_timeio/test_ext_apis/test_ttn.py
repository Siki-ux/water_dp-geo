#! /usr/bin/env python
# -*- coding: utf-8 -*-

import json
import pytest
from unittest.mock import patch
from .conf import CONTENT, mock_thing, mock_response

from timeio import ext_api


def test_no_https_error(mock_thing):
    settings = {"endpoint_uri": "http://endpoint_uri", "api_key": "enc_api_key"}
    thing = mock_thing(settings)
    syncer = ext_api.TtnApiSyncer()
    with pytest.raises(ext_api.NoHttpsError) as r:
        syncer.fetch_api_data(thing, CONTENT)


@pytest.mark.parametrize(
    "value, expected", [(1, 0), (1.1, 0), ("string", 1), ({"key": "val"}, 2), (True, 3)]
)
def test_ttn_dynamic_parameter_mapping(value, expected):
    assert ext_api.TtnApiSyncer.dynamic_parameter_mapping(value) == expected


def test_ttn_dynamic_parameter_mapping_invalid():
    with pytest.raises(ext_api.ExtApiRequestError):
        ext_api.TtnApiSyncer.dynamic_parameter_mapping([1, 2])


@patch("timeio.ext_api.request_with_handling")
@patch("timeio.ext_api.decrypt", return_value="dec_api_key")
@patch("timeio.ext_api.get_crypt_key", return_value="secret")
@patch("timeio.ext_api.json.loads", side_effect=json.loads)
def test_ttn_fetch_api_data(
    mock_json_loads, mock_get_key, mock_decrypt, mock_request, mock_thing, mock_response
):
    raw_json = "\n".join(
        [
            json.dumps(
                {
                    "result": {
                        "uplink_message": {
                            "received_at": "2025-01-01T00:00:00.000000000Z",
                            "decoded_payload": {
                                "param1": 1.1,
                                "param2": "result",
                            },
                        }
                    }
                }
            )
        ]
    )

    mock_request.return_value = mock_response(text=raw_json)
    settings = {"endpoint_uri": "https://endpoint_uri", "api_key": "enc_api_key"}
    thing = mock_thing(settings)
    data = ext_api.TtnApiSyncer().fetch_api_data(thing, CONTENT)
    mock_decrypt.assert_called_once_with("enc_api_key", "secret")
    mock_request.assert_called_once()
    mock_request.assert_called_once_with(
        "GET",
        "https://endpoint_uri",
        headers={"Authorization": "Bearer dec_api_key", "Accept": "text/event-stream"},
    )
    assert "response" in data
    assert isinstance(data["response"], list)
    assert data["url"] == "https://endpoint_uri"


def test_ttn_do_parse():
    api_response = {
        "response": [
            {
                "result": {
                    "uplink_message": {
                        "received_at": "2025-01-01T00:00:00.000000000Z",
                        "decoded_payload": {
                            "param1": 1.1,
                            "param2": "result",
                        },
                    }
                }
            },
            {
                "result": {
                    "uplink_message": {
                        "received_at": "2025-01-01T01:00:00.000000000Z",
                        "decoded_payload": {
                            "param1": 1,
                            "param2": "result",
                        },
                    }
                }
            },
        ],
        "url": "https://api.ttn.test",
    }
    parsed = ext_api.TtnApiSyncer().do_parse(api_response)
    assert len(parsed["observations"]) == 4
    obs = parsed["observations"][0]
    assert json.loads(obs["parameters"])["origin"] == api_response["url"]
    assert "result_number" in obs


def test_ttn_cleanup_json():
    raw = '{"a":1}\n{"b":2}\n'
    expected = '[{"a":1},{"b":2}]'
    result = ext_api.TtnApiSyncer.cleanup_json(raw)
    assert result == expected


def test_ttn_cleanup_json_skips_empty_lines():
    raw = '\n{"a":1}\n\n{"b":2}\n'
    expected = '[{"a":1},{"b":2}]'
    result = ext_api.TtnApiSyncer.cleanup_json(raw)
    assert result == expected


def test_ttn_cleanup_json_empty_input():
    result = ext_api.TtnApiSyncer.cleanup_json("")
    assert result == "[]"
