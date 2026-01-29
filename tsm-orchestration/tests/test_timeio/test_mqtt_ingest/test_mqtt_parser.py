#! /usr/bin/env python
# -*- coding: utf-8 -*-


import pytest
from datetime import datetime


from timeio.parser.mqtt_parser import MqttParser, Observation
from timeio.common import ObservationResultType


class MockParser(MqttParser):
    def do_parse(self, rawdata, origin):
        # Simulate parsing logic
        return [
            Observation(
                timestamp=datetime(2025, 1, 1, 0, 0, 0),
                value=42.0,
                origin=origin,
                position=1,
            ),
            Observation(
                timestamp=datetime(2025, 1, 1, 1, 0, 0),
                value="OK",
                origin=origin,
                position=2,
            ),
            Observation(
                timestamp=datetime(2025, 1, 1, 2, 0, 0),
                value=True,
                origin=origin,
                position=3,
            ),
        ]


@pytest.fixture
def parser():
    return MockParser()


def test_do_parse_returns_observations(parser):
    result = parser.do_parse("raw_data", "mqtt://broker/topic")
    assert len(result) == 3
    assert all(isinstance(obs, Observation) for obs in result)


def test_to_observations_converts_types(parser):
    data = parser.do_parse("data", "origin")
    result = parser.to_observations(data, "thing-uuid")

    assert len(result) == 3

    num = result[0]
    assert num["result_number"] == 42.0
    assert num["result_type"] == ObservationResultType.Number

    string = result[1]
    assert string["result_string"] == "OK"
    assert string["result_type"] == ObservationResultType.String

    boolean = result[2]
    assert boolean["result_boolean"] is True
    assert boolean["result_type"] == ObservationResultType.Bool


def test_invalid_value_raises():
    with pytest.raises(ValueError):
        Observation(timestamp=datetime.now(), value=None, origin="x", position=1)
