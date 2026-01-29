#!/usr/bin/env python3

from unittest import mock, TestCase
import os

import pytest

from timeio.common import get_envvar, get_envvar_as_bool, no_default

TEST_ENV = {
    "VAR_STRING": "test",
    "VAR_INT": "99",
    "VAR_INT_0": "0",
    "VAR_FALSE": "false",
    "VAR_TRUE": "true",
    "VAR_NONE": "None",
    "EMPTY": "",
}

no_cast = None


def is_equal(a, b):
    return type(a) == type(b) and (a == b or a is None and b is None)


# ############################################################
# get_envvar
# ############################################################


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
@pytest.mark.parametrize(
    "name, default, expected",
    [
        ("VAR_STRING", no_default, "test"),
        ("VAR_STRING", "ignored", "test"),
        ("OTHER_VAR", "something", "something"),
    ],
)
def test_get_envvar(name, default, expected):
    result = get_envvar(name, default)
    assert is_equal(result, expected)


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
@pytest.mark.parametrize(
    "name, cast_to, cast_None, expected",
    [
        ("VAR_STRING", no_cast, no_cast, "test"),
        ("EMPTY", no_cast, no_cast, ""),
        ("VAR_INT", no_cast, no_cast, "99"),
        ("VAR_INT", int, no_cast, 99),
        ("VAR_INT", float, no_cast, 99.0),
        ("VAR_FALSE", bool, no_cast, False),
        ("VAR_TRUE", bool, no_cast, True),
        # special casts
        ("EMPTY", bool, no_cast, True),
        ("VAR_STRING", bool, no_cast, True),
        ("VAR_INT_0", bool, no_cast, False),
        # cast 'None'
        ("VAR_NONE", no_cast, True, None),
    ],
)
def test_get_envvar__cast(name, cast_to, cast_None, expected):
    result = get_envvar(name, cast_to=cast_to, cast_None=cast_None)
    assert is_equal(result, expected)


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
@pytest.mark.parametrize(
    "name, cast_to, cast_None, expected",
    [
        ("NOT_SET", no_cast, no_cast, EnvironmentError("Missing .*")),
        ("VAR_STRING", int, no_cast, TypeError("Could not cast .*")),
    ],
)
def test_get_envvar__errors(name, cast_to, cast_None, expected):
    with pytest.raises(type(expected), match=str(expected)):
        get_envvar(name, cast_to=cast_to, cast_None=cast_None)


# ############################################################
# get_envvar_as_bool
# ############################################################
@pytest.mark.parametrize(
    "value, expected",
    [
        ("no", False),
        ("false", False),
        ("fAlSe", False),  # case-insensitive
        ("null", False),
        ("0", False),
        ("None", False),
        ("none", False),  # case-insensitive
        ("", True),
        ("any other value", True),
        (" ", True),
    ],
)
def test_get_envar_as_bool(value, expected):
    with mock.patch.dict(os.environ, {"TEST_VAR": value}, clear=True):
        result = get_envvar_as_bool("TEST_VAR")
    assert is_equal(result, expected)


@pytest.mark.parametrize(
    "value, empty_as_false, expected",
    [
        ("", False, True),  # default
        ("", True, False),
    ],
)
def test_get_envar_as_bool__empty_param(value, empty_as_false, expected):
    with mock.patch.dict(os.environ, {"TEST_VAR": value}, clear=True):
        result = get_envvar_as_bool("TEST_VAR", empty_is_False=empty_as_false)
    assert is_equal(result, expected)


@pytest.mark.parametrize(
    "value, false_list, expected",
    [
        ("not_in_list", ["nix", "nada", "niente"], True),
        ("nada", ["nix", "nada", "niente"], False),
        ("d", list("abcde"), False),
        ("lala", [], True),  # every value is True
    ],
)
def test_get_envar_as_bool__custom_false_list(value, false_list, expected):
    with mock.patch.dict(os.environ, {"TEST_VAR": value}, clear=True):
        result = get_envvar_as_bool("TEST_VAR", false_list=false_list)
    assert is_equal(result, expected)
