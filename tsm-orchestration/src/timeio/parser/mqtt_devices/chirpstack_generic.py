from __future__ import annotations

from typing import Any

from timeio.parser.mqtt_parser import MqttParser, Observation


class ChirpStackGenericParser(MqttParser):
    def do_parse(self, rawdata: Any, origin: str = "", **kwargs) -> list[Observation]:
        timestamp = rawdata["time"]
        out = []
        for key, value in rawdata["object"].items():
            if key == "Data_time":
                # this is a timestamp, we ignore it
                continue
            try:
                out.append(
                    Observation(
                        timestamp=timestamp,
                        value=value,
                        position=key,
                        origin=origin,
                        header=key,
                    )
                )
            except ValueError:
                # value is NaN or None
                continue
        return out
