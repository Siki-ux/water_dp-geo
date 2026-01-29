from __future__ import annotations

import logging
from typing import Any
from grafana_client.client import GrafanaException

logger = logging.getLogger("timeio-grafana-api")


def get_dict_by_key_value(dict_list: list[dict], key: str, value: Any):
    for d in dict_list:
        if d.get(key) == value:
            return d
    return None


def _exists(func: callable, *args) -> bool:
    try:
        func(*args)
    except GrafanaException:
        return False
    else:
        return True
