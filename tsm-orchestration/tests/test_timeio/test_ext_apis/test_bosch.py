#! /usr/bin/env python
# -*- coding: utf-8 -*-

import base64
import pytest
from unittest.mock import patch
from .conf import CONTENT, mock_thing, mock_response

from timeio import ext_api


def test_no_https_error(mock_thing):
    settings = {
        "version": 1,
        "endpoint": "http://bosch.test",
        "sensor_id": "sensor",
        "username": "user",
        "password": "enc_pw",
        "period": 1,
    }
    thing = mock_thing(settings)
    syncer = ext_api.BoschApiSyncer()
    with pytest.raises(ext_api.NoHttpsError) as r:
        syncer.fetch_api_data(thing, CONTENT)


def test_bosch_basic_auth():
    token = ext_api.BoschApiSyncer.basic_auth("user", "pw")
    encoded = token.split(" ")[1]
    assert base64.b64decode(encoded).decode() == "user:pw"


@patch("timeio.ext_api.request_with_handling")
@patch("timeio.ext_api.decrypt", return_value="dec_pw")
@patch("timeio.ext_api.get_crypt_key", return_value="secret_key")
def test_bosch_fetch_api_data(
    mock_get_key, mock_decrypt, mock_request, mock_response, mock_thing
):
    mock_request.return_value = mock_response(
        data=[{"payload": {"observations": ["data"]}}]
    )

    settings = {
        "version": 1,
        "endpoint": "https://bosch.test",
        "sensor_id": "sensor",
        "username": "user",
        "password": "enc_pw",
        "period": 1,
    }
    thing = mock_thing(settings)

    data = ext_api.BoschApiSyncer().fetch_api_data(thing, CONTENT)

    assert isinstance(data, list)
    mock_decrypt.assert_called_once_with("enc_pw", "secret_key")
    mock_request.assert_called_once()
    called_url = mock_request.call_args[0][1]
    assert called_url.startswith("https://bosch.test/sensor/")


def test_bosch_do_parse():
    api_response = [
        {
            "payload": {
                "Type": "DATA",
                "UTC": "2025-05-21T09:12:49.000Z",
                "deviceID": "device_id",
                "param1": 1,
                "param2": 2,
                "param3": 3,
            }
        },
        {
            "payload": {
                "Type": "DATA",
                "UTC": "2025-05-21T09:13:49.000Z",
                "deviceID": "device_id",
                "param1": 3,
                "param2": 2,
                "param3": 1,
            }
        },
    ]
    parsed = ext_api.BoschApiSyncer().do_parse(api_response)
    obs = parsed["observations"][0]
    assert len(parsed["observations"]) == 6
    assert obs["result_number"] == 1
    assert "bosch_data" in obs["parameters"]
