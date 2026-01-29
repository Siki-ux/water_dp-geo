import pytest
from unittest.mock import MagicMock
from timeio import ext_api

CONTENT = {
    "thing": "UUID",
    "datetime_from": "2025-01-01 00:00:00",
    "datetime_to": "2025-01-01 01:00:00",
}


@pytest.fixture
def mock_thing():
    class MockThing:
        def __init__(self, settings):
            self.ext_api = type("ExtApi", (), {"settings": settings})

    return MockThing


@pytest.fixture
def mock_response():
    def _response(status_code=200, data=None, text=None):
        mock = MagicMock()
        mock.status_code = status_code
        mock.json.return_value = data
        mock.text = text
        mock.raise_for_status.side_effect = (
            None if status_code < 400 else ext_api.requests.HTTPError(response=mock)
        )
        return mock

    return _response
