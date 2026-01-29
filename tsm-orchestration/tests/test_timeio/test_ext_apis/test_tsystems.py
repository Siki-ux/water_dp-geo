#! /usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from unittest.mock import patch, MagicMock
from .conf import CONTENT, mock_thing, mock_response

from timeio import ext_api


def test_tsystems_unix_ts_to_str():
    syncer = ext_api.TsystemsApiSyncer()
    ts = 1735689600
    result = syncer.unix_ts_to_str(ts)
    assert result == "2025-01-01 00:00:00"


@patch("timeio.ext_api.request_with_handling")
def test_tsystems_get_bearer_token(mock_request, mock_response):
    mock_request.return_value = mock_response(data={"access_token": "fake_token"})
    syncer = ext_api.TsystemsApiSyncer()
    token = syncer.get_bearer_token("user1", "pass1")
    assert token == "fake_token"
    mock_request.assert_called_once_with(
        "POST",
        syncer.tsytems_auth_url,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_id": "lcmm",
            "grant_type": "password",
            "username": "user1",
            "password": "pass1",
        },
    )


@patch("timeio.ext_api.request_with_handling")
def test_tsystems_get_bearer_token_key_error(mock_request, mock_response):
    mock_request.return_value = mock_response(data={})
    syncer = ext_api.TsystemsApiSyncer()

    with pytest.raises(KeyError):
        syncer.get_bearer_token("user1", "pass1")


@patch("timeio.ext_api.request_with_handling")
@patch("timeio.ext_api.decrypt", return_value="dec_pw")
@patch("timeio.ext_api.get_crypt_key", return_value="secret_key")
def test_tsystems_fetch_api_data(
    mock_get_key, mock_decrypt, mock_request, mock_response, mock_thing
):
    settings = {
        "group": "group",
        "version": 1,
        "password": "enc_pw",
        "username": "user",
        "station_id": "uuid",
    }
    thing = mock_thing(settings)
    syncer = ext_api.TsystemsApiSyncer()
    syncer.get_bearer_token = MagicMock(return_value="bearer_token")
    mock_request.return_value = mock_response(data=[{"data": "ok"}])
    data = syncer.fetch_api_data(thing, CONTENT)

    assert data == [{"data": "ok"}]
    mock_decrypt.assert_called_once_with("enc_pw", "secret_key")
    syncer.get_bearer_token.assert_called_once_with("user", "dec_pw")
    mock_request.assert_called_once()
    args, kwargs = mock_request.call_args
    assert kwargs["headers"]["Authorization"] == "Bearer bearer_token"
    assert kwargs["params"]["aggregationTime"] == "FINEST"


def test_tsytsems_do_parse():
    api_response = [
        {
            "deviceId": "device_id",
            "locationId": "location_id",
            "sendTimestamp": 1730548000,
            "param1": 1,
            "param2": 2,
        },
        {
            "deviceId": "device_id",
            "locationId": "location_id",
            "sendTimestamp": 1730448000,
            "param1": 3,
            "param2": 2,
        },
    ]
    parsed = ext_api.TsystemsApiSyncer().do_parse(api_response)
    obs = parsed["observations"][0]
    assert len(parsed["observations"]) == 4
    assert obs["result_number"] == 1
    assert (
        obs["parameters"]
        == '{"origin": "tsystems_data", "column_header": {"sensor_id": "device_id", "location_id": "location_id", "aggregation_time": "hourly"}}'
    )
