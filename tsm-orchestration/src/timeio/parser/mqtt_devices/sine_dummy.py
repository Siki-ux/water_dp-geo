from __future__ import annotations

from typing import Any
from datetime import datetime, timezone

from timeio.parser.mqtt_parser import MqttParser, Observation


class SineDummyParser(MqttParser):
    def do_parse(self, rawdata: Any, origin: str = "", **kwargs) -> list[Observation]:
        timestamp = datetime.now(tz=timezone.utc)
        return [
            Observation(
                timestamp=timestamp,
                value=rawdata["sine"],
                position=0,
                origin=origin,
                header="sine",
            ),
            Observation(
                timestamp=timestamp,
                value=rawdata["cosine"],
                position=1,
                origin=origin,
                header="cosine",
            ),
        ]
