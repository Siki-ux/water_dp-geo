#!/usr/bin/env python3
from __future__ import annotations

import abc
from typing import TYPE_CHECKING

try:
    # todo: python >= 3.11
    from typing import Self
except ImportError:
    from typing_extensions import Self

if TYPE_CHECKING:
    import pandas as pd


class QcTool(abc.ABC):

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Returns the name of the QcTool"""
        ...

    @property
    @abc.abstractmethod
    def version(self) -> str:
        """Returns the version of the QcTool"""
        ...

    @property
    @abc.abstractmethod
    def columns(self) -> list[str] | pd.Index:
        """
        Property that returns a list of data series names, that
        are currently stored in the QcTool.
        """
        ...

    @abc.abstractmethod
    def check_func_name(self, func_name: str) -> None:
        """
        Checks and returns if the function name is a valid
        qc routine and raise an ValueError otherwise.
        """
        ...

    @abc.abstractmethod
    def add_data(
        self, data: dict[str, pd.Series], quality: dict[str, pd.Series] | None = None
    ):
        """
        Adds data for the next QcTool.execution() call
        """
        ...

    @abc.abstractmethod
    def execute(self, func_name: str, *args, **kwargs) -> Self: ...

    @abc.abstractmethod
    def get_quality(self) -> dict[str, pd.Series]:
        """
        Returns a dict of datetime indexed pandas Series
        containing the quality annotations as STA conform json strings.
        A json string contains the following keys.

        * annotation - The quality annotation,
        * annotationType - name of the tool,
        * properties {
            * version - the package version of the tool,
            * measure - the measure that produced the annotation,
            * userLabel - an optional user given label
        }
        """
        ...

    @abc.abstractmethod
    def get_data(self) -> dict[str, pd.Series]:
        """
        Returns a dict of datetime indexed pandas Series
        containing the data.
        """
        ...
