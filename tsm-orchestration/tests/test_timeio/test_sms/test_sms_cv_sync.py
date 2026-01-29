#!/usr/bin/env python3
import json
import logging
from unittest.mock import patch

import pytest

from timeio.sms import SmsCVSyncer
from time import strptime


def test__SmsCvSyncer_get_utc_str():
    now = SmsCVSyncer.get_utc_str()
    assert isinstance(now, str)
    assert strptime(now, "%Y-%m-%d %H:%M:%S (UTC)")


@pytest.mark.parametrize(
    "data, expected",
    [
        ([], []),
        ([{"id": 1}], [{"id": 1}]),
        ([{"id": 1}, {"id": 1}], [{"id": 1}]),
        ([{"id": 1}, {"id": 2}, {"id": 2}, {"id": 1}], [{"id": 1}, {"id": 2}]),
        ([{"id": 1, "val": "a"}, {"id": 1, "val": "b"}], [{"id": 1, "val": "a"}]),
    ],
)
def test__SmsCvSyncer_remove_id_duplicates(data, expected):
    result = SmsCVSyncer._remove_id_duplicates(data)
    assert result == expected


def test__SmsCvSyncer_remove_id_duplicates__raise_KeyError():
    with pytest.raises(KeyError, match="id"):
        SmsCVSyncer._remove_id_duplicates([{}])


@pytest.mark.parametrize(
    "data, path, expected",
    [
        ({"a": 99}, ["a"], 99),
        ({"a": {"a": 99}}, ["a", "a"], 99),
        ({"a": {"a": 11, "b": 12}, "b": {"a": 21, "b": 22}}, ["a", "a"], 11),
        ({"a": {"a": 11, "b": 12}, "b": {"a": 21, "b": 22}}, ["a", "b"], 12),
        ({"a": {"a": 11, "b": 12}, "b": {"a": 21, "b": 22}}, ["b", "a"], 21),
        ({"a": {"a": 11, "b": 12}, "b": {"a": 21, "b": 22}}, ["b", "b"], 22),
    ],
)
def test__SmsCvSyncer_value_from_dict(data, path, expected):
    result = SmsCVSyncer._value_from_dict(data, path)
    assert result == expected


def test__SmsCvSyncer_value_from_dict__raise_KeyError():
    with pytest.raises(KeyError, match="missing"):
        SmsCVSyncer._value_from_dict({"a": 99}, ["missing"])


def test__SmsCvSyncer_to_postgres_str__warns_deprecated():
    with pytest.deprecated_call():
        SmsCVSyncer._to_postgres_str("foo")


@pytest.mark.parametrize(
    "value, expected",
    [
        (42, 42),
        ("42", 42),  # string ints are converted to ints ...
        ("42.1", "42.1"),  # ... but string floats not
    ],
)
def test__SmsCvSyncer_convert_special(value, expected):
    result = SmsCVSyncer.convert_special(value)
    assert result == expected


@pytest.mark.filterwarnings("ignore:Deprecated method")
@pytest.mark.parametrize(
    "val, expected",
    [
        (None, "NULL"),
        (True, "True"),
        (False, "False"),
        (0, "0"),
        (42, "42"),
        (0.0, "0.0"),
        (0.000, "0.0"),
        (0.0001, "0.0001"),
        (42.3, "42.3"),
        ("42", "42"),  # string ints are converted to ints
        ("foo", "'foo'"),
        ("42.", "'42.'"),  # string floats are converted to strings
        ("42.0001", "'42.0001'"),  # string floats are converted to strings
        ("x'mas", "'x''mas'"),  # single quote escaped
    ],
)
def test__SmsCvSyncer_to_postgres_str(val, expected):
    result = SmsCVSyncer._to_postgres_str(val)
    assert result == expected


@pytest.mark.filterwarnings("ignore:Deprecated method")
def test__SmsCvSyncer_to_postgres_str__raises_TypeError():
    with pytest.raises(TypeError, match="Unconvertible type .*"):
        SmsCVSyncer._to_postgres_str([])  # type: ignore


@pytest.mark.parametrize(
    "data, expected",
    [
        (
            {"name": "empty_table", "keys": {}},
            'CREATE TABLE IF NOT EXISTS "empty_table" ()',
        ),
        (
            {
                "name": "a_table",
                "keys": {
                    "a": {"type": "BIGINT"},
                    "b": {"type": "VARCHAR(200)", "other": "ignored"},
                },
            },
            'CREATE TABLE IF NOT EXISTS "a_table" ("a" BIGINT, "b" VARCHAR(200))',
        ),
    ],
)
def test__SmsCvSyncer_table_create_query(data, expected):
    result = SmsCVSyncer._table_create_query(data)
    assert result.as_string() == expected


@pytest.mark.parametrize(
    "table_dict, data, expected",
    [
        (
            {  # table dict
                "name": "some_table",
                "keys": {
                    "id": {"path": ["id"]},
                    "term": {"path": ["attributes", "term"]},
                },
            },
            [  # data
                {"id": 1, "attributes": {"term": "abc"}},
                {"id": 2, "attributes": {"term": "xyz"}},
            ],
            # expected
            'INSERT INTO "some_table" ("id", "term") VALUES '
            "(1, 'abc'), (2, 'xyz') "
            "ON CONFLICT (id) DO UPDATE SET "
            '"term" = EXCLUDED."term"',
        ),
        (
            {  # table dict
                "name": "TestValuesTable",
                "keys": {
                    "id": {"path": ["id"]},
                    "val1": {"path": ["v1"]},
                    "val2": {"path": ["v2"]},
                    "val3": {"path": ["v3"]},
                },
            },
            [  # data
                {"id": 1, "v1": None, "v2": True, "v3": False},
                {"id": 2, "v1": 0, "v2": 42, "v3": 0.0},
                {"id": 3, "v1": 0.000, "v2": 0.0001, "v3": 42.3},
                {"id": 4, "v1": "a_string", "v2": "with space", "v3": ""},
                {"id": 5, "v1": '"quotes"', "v2": "'quotes'", "v3": "a' quote"},
                {"id": 6, "v1": "42", "v2": "42.", "v3": "42.001"},
            ],
            # expected
            'INSERT INTO "TestValuesTable" ("id", "val1", "val2", "val3") VALUES '
            "(1, NULL, true, false), "
            "(2, 0, 42, 0.0), "
            "(3, 0.0, 0.0001, 42.3), "
            "(4, 'a_string', 'with space', ''), "
            """(5, '"quotes"', '''quotes''', 'a'' quote'), """
            "(6, 42, '42.', '42.001') "
            "ON CONFLICT (id) DO UPDATE SET "
            '"val1" = EXCLUDED."val1", '
            '"val2" = EXCLUDED."val2", '
            '"val3" = EXCLUDED."val3"',
        ),
    ],
)
def test__SmsCvSyncer_table_upsert_query(table_dict, data, expected):
    # hack to bypass init, which works because we just use static methods,
    # within the called function
    syncer = object.__new__(SmsCVSyncer)
    result = syncer._table_upsert_query(table_dict, data)
    assert result.as_string() == expected


@pytest.mark.parametrize(
    "table_dict, exception, errmsg",
    [
        ({}, KeyError, "Missing mandatory top-level field 'keys'"),
        ({"name": "foo"}, KeyError, "Missing mandatory top-level field 'keys'"),
        ({"keys": {}}, KeyError, "Missing mandatory top-level field 'name'"),
        ({"name": "foo", "keys": {}}, KeyError, "Missing mandatory field 'id'"),
    ],
)
def test__SmsCvSyncer_table_upsert_query__raisesErrors(table_dict, exception, errmsg):
    # hack to bypass init, which works because we just use static methods,
    # within the called function
    syncer = object.__new__(SmsCVSyncer)  # hack to bypass init
    with pytest.raises(exception, match=errmsg):
        syncer._table_upsert_query(table_dict, [])


@pytest.mark.parametrize(
    "the_internet",
    [
        # this is a single dict which is passed as one data set to the function
        {
            "https://foo.org/some/end/point": {"data": [1, 2, 3], "other": 42},
            "http://data/1": {"data": [3, 4, 5], "links": {"next": "http://data/2"}},
            "http://data/2": {"data": [5, 6], "links": {"next": "http://data/3"}},
            "http://data/3": {"data": [7, 7], "bar": 99},
        }
    ],
)
@pytest.mark.parametrize(
    "url, expected",
    [
        ("https://foo.org/some/end/point", [1, 2, 3]),
        ("http://data/2", [5, 6, 7, 7]),
        ("http://data/1", [3, 4, 5, 5, 6, 7, 7]),
    ],
)
def test__SmsCvSyncer_get_data_from_url(the_internet, url, expected):

    def urlopen_mock(req):
        """Fake urlopen.

        This is called instead of urllib.request.urlopen and an urllib.request.Request
        object is passed to us. We return a fake Response object, on which `read` can
        be called, which is sufficient for the code we test here.

        Depending on the url (Request.full_url) we return differnt data, which we
        look up in `the_internet` (a dictionary).
        """

        class Response:
            def read(self):
                return json.dumps(the_internet[req.full_url])

        return Response()

    syncer = object.__new__(SmsCVSyncer)  # hack to bypass init
    syncer.logger = logging.getLogger("dummy")
    with patch("timeio.sms.urlopen", urlopen_mock):
        result = syncer.get_data_from_url(url, "")

    assert result == expected
