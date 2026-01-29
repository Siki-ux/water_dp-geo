#!/usr/bin/env python3
import pytest
from timeio.sms import SmsMaterializedViewsSyncer
from psycopg import sql

from unittest.mock import patch

# fmt: off
class ConnOrCursorMock:
    def __init__(self, *args, **kwargs): pass

    def cursor(self, *args, **kwargs): return ConnOrCursorMock()

    def execute(self, *args, **kwargs): return self

    def fetchall(self, *args, **kwargs): pass

    def fetchone(self, *args, **kwargs): pass

    def __enter__(self): return self

    def __exit__(self, *exc): return False
# fmt: on


@pytest.mark.parametrize(
    "materialized_views",
    [
        [],
        ["view1"],
        ["view1", "view2"],
    ],
)
def test_SmsMaterializedViewsSyncer_update_materialized_views(materialized_views):
    with patch("psycopg.connect", ConnOrCursorMock):
        syncer = SmsMaterializedViewsSyncer("host=Fake password=foo")
        syncer.materialized_views = materialized_views
        with patch.object(ConnOrCursorMock, "execute") as mocked_method:
            syncer.update_materialized_views()

    assert mocked_method.call_count == len(materialized_views)
    for i, call in enumerate(mocked_method.mock_calls):
        arg = call.args[0]
        assert isinstance(arg, sql.Composable)
        expected = f'REFRESH MATERIALIZED VIEW CONCURRENTLY "{materialized_views[i]}"'
        assert arg.as_string() == expected


@pytest.mark.parametrize(
    "query_result, expected",
    [
        ([], []),
        ([("view1",)], ["view1"]),
        ([("view1",), ("view2",)], ["view1", "view2"]),
    ],
)
def test_SmsMaterializedViewsSyncer_collect_materialized_views(query_result, expected):

    with patch("psycopg.connect", ConnOrCursorMock):
        syncer = SmsMaterializedViewsSyncer("host=Fake password=foo")
        with patch.object(ConnOrCursorMock, "fetchall", return_value=query_result):
            syncer.collect_materialized_views()

    assert syncer.materialized_views == expected
