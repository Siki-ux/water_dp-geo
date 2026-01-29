#! /usr/bin/env python
# -*- coding: utf-8 -*-

from unittest.mock import patch
from .conf import CONTENT, mock_thing, mock_response

from timeio import ext_api


def test_uba_parse_timeranges():
    date_from, time_from, date_to, time_to = ext_api.UbaApiSyncer.parse_timeranges(
        "2025-01-01 03:00:00", "2025-01-02 04:00:00"
    )
    assert date_from == "2025-01-01"
    assert time_from == 3
    assert date_to == "2025-01-02"
    assert time_to == 4


def test_uba_adjust_datetime():
    result = ext_api.UbaApiSyncer.adjust_datetime("2025-01-01 24:00:00")
    assert result.startswith("2025-01-02")
    assert result.endswith("00:00:00")


@patch("timeio.ext_api.request_with_handling")
def test_uba_get_components_and_scopes(mock_request, mock_response):
    mock_request.side_effect = [
        mock_response(
            data={"1": [1, "NO2"], "2": [2, "PM10"], "count": None, "indices": None}
        ),
        mock_response(data={"10": [10, "hourly"], "20": [20, "daily"], "count": None}),
    ]
    syncer = ext_api.UbaApiSyncer()
    components, scopes = syncer.get_components_and_scopes()

    assert components == {1: "NO2", 2: "PM10"}
    assert scopes == {10: "hourly", 20: "daily"}
    assert mock_request.call_count == 2


@patch("timeio.ext_api.request_with_handling")
def test_uba_get_station_info(mock_request, mock_response):
    mock_request.return_value = mock_response(
        data={
            "data": {
                "A": [10, 1, "station_1"],
                "B": [20, 2, "station_2"],
                "C": [10, 3, "station_1"],
            }
        }
    )
    syncer = ext_api.UbaApiSyncer()
    result = syncer.get_station_info("station_1")

    assert result == [{"scope": 10, "component": 1}, {"scope": 10, "component": 3}]
    mock_request.assert_called_once()


@patch("timeio.ext_api.request_with_handling")
def test_uba_request_measure_endpoint_data_present(mock_request, mock_response):
    mock_request.return_value = mock_response(
        data={"data": {"station1": {"x": ["A", "B", 42, "2025-01-01 00:00:00"]}}}
    )
    syncer = ext_api.UbaApiSyncer()
    result = syncer.request_measure_endpoint(
        "station1", 1, 10, "2025-01-01", "2025-01-02", 0, 1
    )
    assert result == {"x": ["A", "B", 42, "2025-01-01 00:00:00"]}


@patch("timeio.ext_api.request_with_handling")
def test_uba_request_measure_endpoint_data_empty(mock_request, mock_response):
    mock_request.return_value = mock_response(data={"data": {}})
    syncer = ext_api.UbaApiSyncer()
    result = syncer.request_measure_endpoint(
        "station1", 1, 10, "2025-01-01", "2025-01-02", 0, 1
    )
    assert result == {}


@patch.object(ext_api.UbaApiSyncer, "get_station_info")
@patch.object(ext_api.UbaApiSyncer, "request_measure_endpoint")
def test_uba_combine_measure_responses(mock_req, mock_info):
    mock_info.return_value = [{"scope": 10, "component": 1}]
    mock_req.return_value = {"k": ["a", "b", 99, "2025-01-01 00:00:00"]}
    syncer = ext_api.UbaApiSyncer()
    result = syncer.combine_measure_responses(
        "station_1",
        "2025-01-01",
        "2025-01-02",
        0,
        1,
        {1: "NO2"},
        {10: "hourly"},
    )
    assert result == [
        {"timestamp": "2025-01-01 00:00:00", "value": 99, "measure": "NO2 hourly"}
    ]


def test_uba_parse_measure_data_basic():
    data = [
        {"timestamp": "2025-01-01 01:00:00", "value": 5.5, "measure": "NO2 hourly"},
        {"timestamp": "2025-01-01 24:00:00", "value": 10, "measure": "PM10 daily"},
    ]
    syncer = ext_api.UbaApiSyncer()
    parsed = syncer.parse_measure_data(data, "station_1")
    assert len(parsed) == 2
    assert parsed[0]["datastream_pos"] == "NO2 hourly"
    assert parsed[1]["result_number"] == 10
    assert "uba_data" in parsed[0]["parameters"]


@patch("timeio.ext_api.request_with_handling")
def test_uba_get_airquality_data(mock_request, mock_response):
    mock_request.return_value = mock_response(
        data={
            "data": {
                "station_1": {
                    "a": [
                        "2025-01-01 00:00:00",
                        55,
                        True,
                        [1, "NO2", 10],
                        [2, "PM10", 20],
                    ]
                }
            }
        }
    )
    components = {1: "NO2", 2: "PM10"}
    syncer = ext_api.UbaApiSyncer()
    result = syncer.get_airquality_data(
        "station_1", "2025-01-01", "2025-01-02", 0, 1, components
    )
    assert len(result) == 1
    entry = result[0]
    assert entry["airquality_index"] == 55
    assert entry["pollutant_info"][0]["component"] == "NO2"
    assert entry["pollutant_info"][1]["airquality_index"] == 20


def test_uba_parse_aqi_data_basic():
    aqi_data = [
        {
            "timestamp": "2025-01-01 00:00:00",
            "airquality_index": 42,
            "data_complete": True,
            "pollutant_info": [{"component": "NO2", "airquality_index": 10}],
        },
        {
            "timestamp": "2025-01-01 24:00:00",
            "airquality_index": 11,
            "data_complete": True,
            "pollutant_info": [{"component": "PM10", "airquality_index": 20}],
        },
    ]
    syncer = ext_api.UbaApiSyncer()
    parsed = syncer.parse_aqi_data(aqi_data, "station_1")
    assert len(parsed) == 2
    assert parsed[0]["result_number"] == 42
    assert parsed[1]["result_number"] == 11
    assert "AQI" in parsed[0]["datastream_pos"]


@patch.object(ext_api.UbaApiSyncer, "get_components_and_scopes")
@patch.object(ext_api.UbaApiSyncer, "combine_measure_responses")
@patch.object(ext_api.UbaApiSyncer, "get_airquality_data")
def test_uba_fetch_api_data(mock_aqi, mock_meas, mock_comps, mock_thing):
    mock_comps.return_value = ({"1": "NO2"}, {"10": "hourly"})
    mock_meas.return_value = [{"timestamp": "2025-01-01", "value": 1, "measure": "NO2"}]
    mock_aqi.return_value = [{"timestamp": "2025-01-01", "airquality_index": 42}]
    settings = {"station_id": "station_1"}
    thing = mock_thing(settings)

    result = ext_api.UbaApiSyncer().fetch_api_data(thing, CONTENT)
    assert result["station_id"] == "station_1"
    assert "measure_data" in result
    assert "aqi_data" in result
    mock_comps.assert_called_once()
    mock_meas.assert_called_once()
    mock_aqi.assert_called_once()
