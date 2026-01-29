from __future__ import annotations

from typing import Any

from timeio.parser.mqtt_parser import MqttParser, Observation


class BrightskyDwdApiParser(MqttParser):
    def do_parse(self, rawdata: Any, origin: str = "", **kwargs) -> list[Observation]:
        weather = rawdata["weather"]
        timestamp = weather.pop("timestamp")
        source = rawdata["sources"][0]
        out = []
        for prop, value in weather.items():
            try:
                out.append(
                    Observation(
                        timestamp=timestamp,
                        value=value,
                        position=prop,
                        origin=origin,
                        header=source,
                    )
                )
            except ValueError:  # value is NaN or None
                continue

        return out
