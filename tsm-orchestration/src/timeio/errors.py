#!/usr/bin/env python3
from __future__ import annotations


class ParsingError(RuntimeError):
    """Parsing failed."""

    pass


class ProcessingError(RuntimeError):
    """
    Processing failed
    """

    pass


class ParsingWarning(RuntimeWarning):
    """
    Report parsing issues not severe enough to abort the process.
    """

    pass


class UploadError(IOError):
    """
    Upload failed
    """

    pass


# =====================================================================
# Errors that are handled gracefully in base_handler.AbstractHandler
# =====================================================================


class DataNotFoundError(RuntimeError):
    """
    Data is missing.
    Handled gracefully in base_handler.AbstractHandler
    """

    pass


class NoDataWarning(RuntimeWarning):
    """
    Data is not present.
    Handled gracefully in base_handler.AbstractHandler

    Added in version 0.4.0
    """

    pass


class UserInputError(ParsingError):
    """
    Error that originated by malformed data or input provided by a user.
    Handled gracefully in base_handler.AbstractHandler

    Added in version 0.6.0
    """

    pass
