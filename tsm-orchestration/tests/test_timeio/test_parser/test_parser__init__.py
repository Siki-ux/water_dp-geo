#!/usr/bin/env python3


import pytest

from timeio.parser import (
    get_parser,
    CsvParser,
    JsonParser,
    CampbellCr6Parser,
    BrightskyDwdApiParser,
    YdocMl417Parser,
    ChirpStackGenericParser,
    SineDummyParser,
    AbcParser,
    _default_settings,
)


@pytest.mark.parametrize(
    "parser_type, expected_type, expected_attrs",
    [
        ("csvparser", CsvParser, {"settings": dict}),
        ("jsonparser", JsonParser, {"settings": dict, "normalize_kws": dict}),
        ("campbell_cr6", CampbellCr6Parser, {}),
        ("brightsky_dwd_api", BrightskyDwdApiParser, {}),
        ("ydoc_ml417", YdocMl417Parser, {}),
        ("chirpstack_generic", ChirpStackGenericParser, {}),
        ("sine_dummy", SineDummyParser, {}),
    ],
)
def test__get_parser__type(parser_type, expected_type, expected_attrs):
    parser = get_parser(parser_type, {})
    assert isinstance(parser, AbcParser)
    assert isinstance(parser, expected_type)
    for attr_name, typ in expected_attrs.items():
        assert hasattr(parser, attr_name)
        attr = getattr(parser, attr_name)
        assert isinstance(attr, typ)


def test__get_parser__unknown_type():
    with pytest.raises(NotImplementedError, match="parser .* not known$"):
        get_parser("NonExistentType", {})


CSV_DEFAULT_SETTINGS = _default_settings[CsvParser]
JSON_DEFAULT_SETTINGS = _default_settings[JsonParser]


@pytest.mark.parametrize(
    "parser_type, settings, expected",
    [
        ("csvparser", {}, CSV_DEFAULT_SETTINGS),
        ("csvparser", None, CSV_DEFAULT_SETTINGS),
        ("csvparser", {"newkey": "spam"}, CSV_DEFAULT_SETTINGS | {"newkey": "spam"}),
        ("csvparser", {"header": "new"}, CSV_DEFAULT_SETTINGS | {"header": "new"}),
        (
            "csvparser",
            {"pandas_read_csv": {"newkey": "spam"}},
            CSV_DEFAULT_SETTINGS | {"newkey": "spam"},
        ),
        (
            "csvparser",
            {"pandas_read_csv": {"header": "new"}},
            CSV_DEFAULT_SETTINGS | {"header": "new"},
        ),
        (
            "csvparser",
            {"header": "b", "pandas_read_csv": {"header": "a"}},
            CSV_DEFAULT_SETTINGS | {"header": "a"},
        ),
        (
            "csvparser",
            {"header": "b", "pandas_read_csv": None},
            CSV_DEFAULT_SETTINGS | {"header": "b"},
        ),
        # JSON PARSER
        ("jsonparser", {}, JSON_DEFAULT_SETTINGS),
        ("jsonparser", None, JSON_DEFAULT_SETTINGS),
        ("jsonparser", {"newkey": "spam"}, JSON_DEFAULT_SETTINGS | {"newkey": "spam"}),
        ("jsonparser", {"header": "new"}, JSON_DEFAULT_SETTINGS | {"header": "new"}),
        (
            # pandas_json_normalize keywords are NOT merged with settings, in contrary
            # to pandas_read_csv with the CSV parser. Instead, the normalisation
            # keywords are stored as attribute within the class (see JsonParser.normalize_kws)
            "jsonparser",
            {"pandas_json_normalize": {"newkey": "spam"}},
            JSON_DEFAULT_SETTINGS,
        ),
    ],
)
def test__get_parser__settings(parser_type, settings, expected):
    parser = get_parser(parser_type, settings)
    assert parser.settings == expected
