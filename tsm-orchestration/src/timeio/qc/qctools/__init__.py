#!/usr/bin/env python3

from .abc_tool import QcTool
from .saqc_tool import Saqc


def get_qctool(name) -> type[QcTool]:
    if name == "saqc":
        return Saqc
    raise NotImplementedError(f"No QC tool with name {name}")
