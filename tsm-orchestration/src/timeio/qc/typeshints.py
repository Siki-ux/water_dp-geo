#!/usr/bin/env python3
from __future__ import annotations
import typing
import datetime

if typing.TYPE_CHECKING:
    import pandas as pd

    TimestampT = datetime.datetime | pd.Timestamp
    WindowT = int | pd.Timedelta
