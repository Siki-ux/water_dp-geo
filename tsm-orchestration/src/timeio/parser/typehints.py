from __future__ import annotations

from typing import TypedDict
from typing_extensions import Required
from timeio.typehints import JsonT


class ObservationPayloadT(TypedDict, total=False):
    phenomenon_time_start: str
    phenomenon_time_end: str
    result_time: Required[str]
    result_type: Required[int]
    result_number: float | int
    result_string: str
    result_boolean: bool
    result_json: JsonT
    result_latitude: float | int
    result_longitude: float | int
    result_altitude: float | int
    result_quality: JsonT
    valid_time_start: str
    valid_time_end: str
    parameters: JsonT
    datastream_pos: Required[str]
