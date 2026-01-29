#!/usr/bin/env python3
from __future__ import annotations

import logging as _logging
from functools import wraps as _wraps
from typing import Literal as _Literal
from typing import Union as _Union
from typing import cast as _cast
from warnings import warn as _warn

try:
    import psycopg as _psycopg
    from psycopg import sql as _sql
except ImportError as e:
    raise EnvironmentError(
        f"To use the module {__package__}.{__name__} psycopg 3 is needed."
        f"Install it with 'pip install psycopg[binary]'"
    )

# Keep the original function, in case the monkey-patch
# is executed multiple times.
__psycopgCursorExecute = _psycopg.Cursor.execute
__patched = False
_ConOrCurT = _Union[_psycopg.Connection, _psycopg.Cursor]


def log_psycopg_query(
    logger: _logging.Logger,
    conn_or_cur: _ConOrCurT,
    query,
    params=None,
    log_level=_logging.DEBUG,
):
    msg, q = None, query
    if isinstance(q, str):
        q = _sql.SQL(_cast(_Literal, q.strip()))
    if isinstance(q, _sql.Composable):
        msg = f"\n\tQUERY: %r\n\tPARAMS: %s"
        log_args = [q.as_string(conn_or_cur)]
        if params is None:
            log_args.append("--")
        else:
            log_args.append(params)
        logger.log(log_level, msg, *log_args)


def monkey_patch_psycopg_execute_to_log_sql_queries(
    logger: _logging.Logger, log_level: int | str = "DEBUG"
):
    if isinstance(log_level, str):
        log_level = _logging.getLevelName(log_level)
    if not isinstance(log_level, int):
        raise ValueError(
            f"log_level must be an integer, or one of the default string levels, "
            f"not {log_level}"
        )

    global __patched
    if __patched:
        _warn(
            "monkey_patch_psycopg_execute_to_log_sql_queries() "
            "should only called once, to monkey-patch 'psycopg.Cursor.execute'. ",
            stacklevel=2,
        )
    else:
        __patched = True

    def patch(func: callable) -> callable:
        @_wraps(func)
        def wrapper(self: _ConOrCurT, query, params=None, **kwargs):
            # guard prevents unnecessary processing
            if logger.isEnabledFor(log_level):
                log_psycopg_query(logger, self, query, params, log_level=log_level)
            return func(self, query, params, **kwargs)

        return wrapper

    _psycopg.Cursor.execute = patch(__psycopgCursorExecute)
