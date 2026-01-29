from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar

from timeio.parser.typehints import ObservationPayloadT

parsedT = TypeVar("parsedT")


class AbcParser(ABC):
    @abstractmethod
    def do_parse(self, *args) -> parsedT:
        raise NotImplementedError

    @abstractmethod
    def to_observations(self, *args) -> list[ObservationPayloadT]:
        raise NotImplementedError
