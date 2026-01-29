#!/usr/bin/env python3
from __future__ import annotations

import enum
import logging
import logging.config
import os
from typing import Any, Literal

no_default = type("no_default", (), {})


class ObservationResultType(enum.IntEnum):
    Number = 0
    String = 1
    Json = 2
    Bool = 3


# todo: For python >= 3.11 use StrEnum
# todo: For python >= 3.13 use EnumDict
class ObservationResultFieldName:
    ResultNumber = "result_number"
    ResultString = "result_string"
    ResultJson = "result_json"
    ResultBool = "result_bool"


def get_result_field_name(
    result_type: ObservationResultType, errors: Literal["raise", "ignore"] = "ignore"
) -> ObservationResultFieldName | None:
    """Return the column name of the observation table, where the data
    of a given type must be stored.

    See also ->ObservationResultFieldName and ->ObservationResultType.
    """
    field_name = {
        ObservationResultType.Number: ObservationResultFieldName.ResultNumber,
        ObservationResultType.String: ObservationResultFieldName.ResultString,
        ObservationResultType.Json: ObservationResultFieldName.ResultJson,
        ObservationResultType.Bool: ObservationResultFieldName.ResultBool,
    }.get(result_type, None)
    if field_name is None and errors == "raise":
        raise ValueError(f"Unknown Observation.ResultType {result_type}")
    return field_name


def get_envvar(name, default: Any = no_default, cast_to: type = None, cast_None=True):
    val = os.environ.get(name)
    if val is None:
        if default is no_default:
            raise EnvironmentError(f"Missing environment variable {name!r}.")
        return default
    elif val == "None" and cast_None:
        return None
    elif cast_to is not None:
        try:
            if cast_to is bool:
                return get_envvar_as_bool(name)
            return cast_to(val)
        except Exception:
            raise TypeError(
                f"Could not cast environment variable {name!r} "
                f"to {cast_to}. Value: {val}"
            ) from None
    return val


def get_envvar_as_bool(
    name, false_list=("no", "false", "0", "null", "none"), empty_is_False: bool = False
) -> bool:
    """
    Return True if an environment variable is set and its value
    is not in the false_list.
    Return False if an environment variable is unset or if its value
    is in the false_list.

    If 'empty_is_False' is True:
        Same logic as above, but an empty string is considered False

    The false_list is not case-sensitive. (faLsE == FALSE = false)
    """
    val = os.environ.get(name, None)
    if val is None:
        return False
    if val == "":
        return not empty_is_False
    return val.lower() not in false_list


def log_query(logger: logging.Logger, query: str, params: Any = no_default):
    """
    Log a string(!) query.

    Note that this has no dependencies to any database package at all.
    For a more detailed logging see:
     - utils.psycopg_helper.log_psycopg_query
     - utils.psycopg_helper.monkey_patch_psycopg_execute_to_log_sql_queries
    """
    if not isinstance(query, str):
        raise TypeError(f"query must be string not {type(query)}")

    args = [query]
    if params is no_default:
        args.append("--")
    else:
        args.append(params)
    logger.debug(f"\n\tQUERY: %r\n\tPARAMS: %s", *args)


def setup_logging(log_level="INFO"):
    """
    Setup logging.

    Globally setup logging according to utils.common.LOGGING_CONFIG
    and set the log level of the root logger to the given level.
    """

    format = (
        "[%(asctime)s] %(process)s %(levelname)-6s %(name)s: %(funcName)s: %(message)s"
    )
    logging.basicConfig(
        level=log_level,
        format=format,
        datefmt="%Y-%m-%d %H:%M:%S",
    )
