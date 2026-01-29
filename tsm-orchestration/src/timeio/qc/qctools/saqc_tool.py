#!/usr/bin/env python3
from __future__ import annotations

import json
import warnings
from typing import Any

import numpy as np
import pandas as pd
import saqc
from saqc import DictOfSeries

from timeio.qc.qctools import QcTool

try:
    import tsm_user_code  # noqa, this registers user functions on SaQC
except ImportError:
    warnings.warn("could not import module 'tsm_user_code'")

QUALITY_COLUMNS = ["annotationType", "annotation", "measure", "userLabel", "version"]
#                  "saqc"             flag         func       label        saqc.version


class STAMPLATEScheme(saqc.FloatScheme):

    @staticmethod
    def toSTAannotations(row: pd.Series) -> dict[str, str | dict[str, str]]:
        """Create a dict that can be translated to a structured json according to
        the STAMPLATE specs."""
        return {
            "annotationType": row["annotationType"],
            "annotation": str(row["annotation"]),
            "properties": {
                "measure": row["measure"],
                "userLabel": row["userLabel"],
                "version": row["version"],
            },
        }

    @staticmethod
    def fromSTAannotations(s: pd.Series[dict]) -> pd.DataFrame:
        """Make a pandas.Dataframe with QUALITY_COLUMNS from a pandas.Series with
        timeIO/STA standard quality labels (dicts parsed from a structured JSON).
        """
        df = pd.json_normalize(list(s))
        df.index = s.index
        if df.empty:
            df = df.reindex(columns=QUALITY_COLUMNS)
        df.columns = df.columns.str.removeprefix("properties.")
        return df[QUALITY_COLUMNS]

    def toInternal(self, flags: saqc.DictOfSeries) -> saqc.Flags:
        """Translate a dict of pandas.Series of json quality annotations
        to a Flags object with a History (with metadata) for each series.
        """

        data = {}
        for key, series in flags.items():  # type: str, pd.Series
            df: pd.DataFrame = self.fromSTAannotations(series)
            history = saqc.core.History(index=df.index)
            for (anno, measure, user_label), values in df.groupby(
                ["annotation", "measure", "userLabel"]
            ):
                column = pd.Series(np.nan, index=df.index)
                column.loc[values.index] = self(anno)
                kwargs = {"label": user_label}
                history.append(column, meta={"func": measure, "kwargs": kwargs})
            data[key] = history
        return saqc.Flags(data)

    def toExternal(
        self, flags: saqc.Flags, attrs: dict | None = None
    ) -> saqc.DictOfSeries:
        """
        Translate from internal Flags object with multiple Histories (with metadata)
        to a dict of pandas.Dataframes, each with QUALITY_COLUMNS.
        """
        UNFLAGGED = saqc.UNFLAGGED  # noqa
        out = saqc.DictOfSeries()

        tflags = super().toExternal(flags, attrs=attrs)
        for field in tflags.columns:
            series: pd.Series = tflags[field]
            # The df has the index from series.
            df = pd.DataFrame(
                {
                    "annotationType": Saqc.name,
                    "annotation": series,
                    "version": Saqc.version,
                    "measure": "",  # filled below
                    "userLabel": "",  # filled below
                }
            )

            assert set(df.columns) == set(QUALITY_COLUMNS)

            history = flags.history[field]
            for col in history.columns:
                # We map the meta entries (func and label) to the respective rows
                valid = (history.hist[col] != UNFLAGGED) & history.hist[col].notna()
                meta = history.meta[col]
                df.loc[valid, "measure"] = meta["func"]
                df.loc[valid, "userLabel"] = meta["kwargs"].get("label", None)
                series = pd.Series(index=df.index, dtype=object)
                if not df.empty:
                    series = df.apply(self.toSTAannotations, axis=1)
                out[field] = series

        return out


class Saqc(QcTool):

    name = "saqc"
    version = saqc.__version__

    def __init__(self):
        self._qc = saqc.SaQC(scheme=STAMPLATEScheme())

    @property
    def columns(self) -> pd.Index:
        return self._qc.columns

    def check_func_name(self, func_name: str):
        if not hasattr(saqc.SaQC, func_name):
            raise ValueError(f"Unknown qc routine {func_name} for SaQC")

    def execute(self, func_name: str, *args, **kwargs) -> Saqc:
        qc = self._qc
        func = getattr(qc, func_name)
        self._qc = func(*args, **kwargs)
        return self

    def add_data(
        self, data: dict[str, pd.Series], quality: dict[str, pd.Series] | None = None
    ):
        if quality is not None:
            quality = DictOfSeries(quality)

        # If quality is not None we will end up in STAMPLATEScheme.toInternal
        # which then do the parsing of the STA-json annotations.
        new = saqc.SaQC(DictOfSeries(data), quality, scheme=STAMPLATEScheme())
        self._qc[new.columns] = new

    def get_quality(self) -> dict[str, pd.Series]:
        # The back translation to STA-compatible json annotations is
        # done in the STAMPLATEScheme.toExternal .
        return self._qc.flags  # type: ignore

    def get_data(self) -> dict[str, pd.Series]:
        return self._qc.data  # type: ignore
