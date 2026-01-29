#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations


import json
import logging
import warnings


from abc import abstractmethod
from typing import Any, cast
from datetime import datetime

import pandas as pd

from timeio.parser.abc_parser import AbcParser
from timeio.parser.typehints import ObservationPayloadT
from timeio.common import ObservationResultType
from timeio.errors import ParsingError


class PandasParser(AbcParser):
    def __init__(self, settings: dict[str, Any]):
        self.logger = logging.getLogger(self.__class__.__qualname__)
        self.settings = settings
        name = self.__class__.__name__
        self.logger.debug(f"parser settings in use with {name}: {self.settings}")

    @abstractmethod
    def do_parse(
        self, rawdata: Any, project_name: str, thing_uuid: str
    ) -> pd.DataFrame:
        raise NotImplementedError

    def to_observations(
        self, data: pd.DataFrame, origin: str, parser_uuid: str | None = None
    ) -> list[ObservationPayloadT]:
        observations = []

        data.index.name = "result_time"
        data.index = data.index.map(lambda ts: ts.isoformat())

        to_process = [val for _, val in data.items()]

        while to_process:
            chunk = to_process.pop()
            col = str(chunk.name)
            if pd.api.types.is_numeric_dtype(chunk):
                chunk.name = "result_number"
                result_type = ObservationResultType.Number
            elif pd.api.types.is_bool_dtype(chunk):
                chunk.name = "result_bool"
                result_type = ObservationResultType.Bool
            elif pd.api.types.is_object_dtype(chunk):
                # we need to handle object columns with special care

                # try to seperate out numerical values to account for data (transmission) errors
                numeric_chunk = cast(pd.Series, pd.to_numeric(chunk, errors="coerce"))
                if numeric_chunk.isna().all():
                    # no numerical values found, we have a string only column
                    chunk.name = "result_string"
                    result_type = ObservationResultType.String
                else:
                    # numerical values found -> the column consists of mixed data types, currently
                    # we only distinguish between numerical and string values, this could be
                    # improved in the future
                    str_chunk = cast(
                        pd.Series, chunk.loc[numeric_chunk.isna()].str.strip()
                    )
                    to_process.extend((numeric_chunk, str_chunk))
                    continue
            else:
                raise ParsingError(
                    f"Data of type {chunk.dtype} is not supported. "
                    f"In {origin or 'datafile'}, column {col}"
                )

            # we don't want to write NaN
            chunk = chunk.dropna()
            # add metadata
            chunk = chunk.reset_index()
            chunk["result_type"] = result_type
            chunk["datastream_pos"] = str(col)
            chunk["parameters"] = json.dumps(
                {
                    "origin": origin,
                    "column_header": col,
                    "parsed_at": datetime.now().isoformat(),
                    "parser_id": parser_uuid,
                }
            )

            observations.extend(chunk.to_dict(orient="records"))
        return observations
