#! /usr/bin/env python

import pytest
from datetime import datetime
from timeio.parser.mqtt_devices.brightsky_dwd import BrightskyDwdApiParser
from timeio.parser.mqtt_devices.campbell_cr6 import CampbellCr6Parser
from timeio.parser.mqtt_devices.chirpstack_generic import ChirpStackGenericParser
from timeio.parser.mqtt_devices.ydoc_ml_417 import YdocMl417Parser


def test_brightsky_parser_basic():
    parser = BrightskyDwdApiParser()
    raw = {
        "weather": {"timestamp": "2025-01-01T00:00:00Z", "temp": 20, "humidity": 50},
        "sources": ["api_source"],
    }
    obs = parser.do_parse(raw, origin="test/origin")
    assert len(obs) == 2
    assert obs[0].origin == "test/origin"
    assert obs[0].header == "api_source"


def test_campbell_parser_basic():
    parser = CampbellCr6Parser()
    raw = {
        "properties": {
            "loggerID": "CR6_18341",
            "observationNames": ["Batt_volt_Min", "PTemp"],
            "observations": {"2022-05-24T08:53:00Z": [11.9, 26.91]},
        }
    }
    obs = parser.do_parse(raw, origin="device/topic")
    assert len(obs) == 2
    assert obs[0].header == "Batt_volt_Min"
    assert obs[1].header == "PTemp"


def test_chirpstack_parser_basic():
    parser = ChirpStackGenericParser()
    raw = {
        "time": "2025-01-01T00:00:00Z",
        "object": {"temp": 20, "humidity": 50, "Data_time": "ignore_me"},
    }
    obs = parser.do_parse(raw, origin="chirp/test")
    assert len(obs) == 2
    assert all(o.header in ["temp", "humidity"] for o in obs)


def test_ydoc_ml417_parser_only_data_jsn():
    parser = YdocMl417Parser()
    assert parser.do_parse({"data": []}, origin="something") == []


def test_ydoc_ml417_parser_valid():
    parser = YdocMl417Parser()
    raw = {
        "data": [
            {
                "$ts": 250101000000,
                "MINVi": 1.0,
                "AVGVi": 3,
                "AVGCi": 100,
                "P1*": "0*T",
                "P2": "0*T",
                "P3": "0*T",
                "P4": "0*T",
            }
        ]
    }
    obs = parser.do_parse(raw, origin="data/jsn")
    assert len(obs) == 7
    assert isinstance(obs[0].timestamp, datetime)
