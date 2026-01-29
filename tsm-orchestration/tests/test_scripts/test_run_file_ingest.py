#!/usr/bin/env python3

import pytest

from run_file_ingest import ParserJobHandler


@pytest.mark.parametrize(
    "content, expected",
    [
        ({"EventName": "s3:something"}, False),
        ({"EventName": "s3:ObjectCreated:Put"}, True),
        ({"EventName": "s3:ObjectCreated:CompleteMultipartUpload"}, True),
    ],
)
def test__ParserJobHandler_is_valid_event(content, expected):
    result = ParserJobHandler.is_valid_event(content)
    assert result == expected


@pytest.mark.parametrize(
    "content, expected",
    [
        ({}, KeyError("EventName")),
        (None, TypeError(".* object is not subscriptable$")),
        (99, TypeError(".* object is not subscriptable$")),
    ],
)
def test__ParserJobHandler_is_valid_event__raises(content, expected):
    with pytest.raises(type(expected), match=str(expected)):
        ParserJobHandler.is_valid_event(content)
