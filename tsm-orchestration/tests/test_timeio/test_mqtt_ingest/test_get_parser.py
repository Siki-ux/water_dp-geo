#! /usr/bin/env python

import pytest
from timeio.parser import get_parser
from timeio.parser.mqtt_devices.campbell_cr6 import CampbellCr6Parser


def test_get_parser_mqtt_specific():
    parser = get_parser("campbell_cr6", None)
    assert isinstance(parser, CampbellCr6Parser)


def test_get_parser_invalid():
    with pytest.raises(NotImplementedError):
        get_parser("unknown_parser", None)
