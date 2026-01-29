#! /usr/bin/env python
# -*- coding: utf-8 -*-

from unittest.mock import patch
from .conf import CONTENT, mock_thing, mock_response

from timeio import ext_api


@patch("timeio.ext_api.request_with_handling")
def test_dwd_fetch_api_data(mock_request, mock_response, mock_thing):
    mock_request.return_value = mock_response(data={"weather": []})
    settings = {"station_id": "station_id"}
    thing = mock_thing(settings)
    result = ext_api.DwdApiSyncer().fetch_api_data(thing, CONTENT)
    mock_request.assert_called_once()
    called_args, called_kwargs = mock_request.call_args
    assert called_args[0] == "GET"
    assert called_args[1] == ext_api.DwdApiSyncer.brightsky_base_url
    assert called_kwargs["params"]["dwd_station_id"] == "station_id"
    assert result == {"weather": []}


def test_dwd_do_parse():
    api_response = {
        "weather": [
            {
                "timestamp": "2025-01-01T00:00:00Z",
                "temperature": 5.1,
                "condition": "rain",
                "fallback_source_ids": None,
                "source_id": 123,
            },
            {
                "timestamp": "2025-01-01T01:00:00Z",
                "temperature": None,
                "condition": "rain",
                "source_id": 123,
            },
        ],
        "sources": [
            {
                "id": 1,
                "dwd_station_id": "station_id",
                "lat": 51.0,
                "lon": 11.0,
            }
        ],
    }
    syncer = ext_api.DwdApiSyncer()
    parsed = syncer.do_parse(api_response)
    obs = parsed["observations"][1]
    assert len(parsed["observations"]) == 3
    assert obs["result_string"] == "rain"
    assert "dwd_data" in obs["parameters"]
