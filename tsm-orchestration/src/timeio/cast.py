#!/usr/bin/env python3
from __future__ import annotations

from typing import Any, Iterable, TypeVar
from datetime import datetime, timezone
import pandas as pd


def flatten_nested_str_list(obj: Any) -> list[str] | None:
    """
    Flatten an arbitrary nested list of strings to a simple flat list.

    If any element is not a list and nor a string the function
    return None.

    See also function `flatten()`.
    """
    return flatten(obj, lambda e: isinstance(e, str), (list,))


def flatten(
    obj: Any,
    element_test: callable = lambda x: True,
    list_types: Iterable[type] = (list, tuple),
) -> list | None:
    """
    Flatten an arbitrary nested list to a simple flat list.
    If any non-list element fails the element_test the
    function returns None.

    Example:
    - flatten_nested_list('99') -> None
    - flatten_nested_list(['99', [['la'], [666]]]) -> ['99', 'la', 666]
    - flatten_nested_list(['99', [['la'], [666]]], lambda e: isinstance(e,str)) -> None
    - flatten_nested_list(['99', [['la']]], lambda e: isinstance(e,str)) -> ['99', 'la']
    """
    flat = []
    if not isinstance(obj, tuple(list_types)):
        return None
    for elem in obj:
        if isinstance(elem, tuple(list_types)):
            if (li := flatten(elem, element_test, list_types)) is None:
                return None
            flat += li
        elif element_test(elem):
            flat.append(elem)
        else:
            return None
    return flat


DtWithTZ = TypeVar("DtWithTZ", bound=pd.Timestamp | pd.DatetimeIndex | datetime)


def rm_tz(obj: DtWithTZ) -> DtWithTZ:
    """If the given object has a timezone we localize it to UTC and
    remove the timezone information. Objects that have no timezone
    information in the first place are returned as they are."""

    if isinstance(obj, datetime):
        if obj.tzinfo is None:
            return obj
        return obj.astimezone(timezone.utc).replace(tzinfo=None)

    if isinstance(obj, (pd.Timestamp, pd.DatetimeIndex)):
        if obj.tz is None:
            return obj
        return obj.tz_convert("UTC").tz_localize(None)

    raise TypeError(f"Unsupported type {type(obj).__qualname__}")
