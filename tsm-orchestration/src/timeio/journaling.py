#!/usr/bin/env python3

from __future__ import annotations

import json
import logging
import warnings
from datetime import datetime, timezone
from http.client import HTTPResponse
from typing import Literal
from urllib import request
from urllib.error import HTTPError

from timeio.common import get_envvar, get_envvar_as_bool

__all__ = ["Journal"]
logger = logging.getLogger("journaling")


class Journal:
    def __init__(
        self,
        name: str,
        errors: Literal["raise", "warn", "ignore"] = "raise",
    ):
        """
        Class to send messages to the user journal.

        The journal offers three modes of operation, which can be chosen by the
        argument `errors`.

        For a systems where journaling is curial, use `errors='raise'` (default)
        and every error is raised immediately. For example if the journal-endpoint
        (database-API) is not reachable or if a thing-UUID does not exist an error
        will be raised. It is the duty of the caller to handle the error accordingly.

        For a systems where journaling is less important, one can use `errors='warn'`,
        which will cause the Journal to emit a warning in case of errors, but will
        not disturb the program flow in other ways.

        If journaling is even less important one could use `errors='ignore'`,
        which will cause the Journal to be silent in case of errors.

        Added in version 0.4.0
        """

        if errors not in ["raise", "warn", "ignore"]:
            raise ValueError('error must be one of ["raise", "warn", "ignore"]')
        self.error_strategy = errors
        self.name = name
        self.enabled = get_envvar_as_bool("JOURNALING")
        self.base_url = get_envvar("DB_API_BASE_URL", None)

        if not self.enabled:
            warnings.warn(
                "Journaling is disabled. To enable it, "
                "set environment variables 'JOURNALING' "
                "and 'DB_API_BASE_URL'",
                RuntimeWarning,
                stacklevel=2,
            )
            return

        if self.base_url is None:
            raise EnvironmentError(
                "If JOURNALING is enabled, environment "
                "variable DB_API_BASE_URL must be set."
            )
        # check if up
        with request.urlopen(f"{self.base_url}/health") as resp:
            if resp.status != 200:
                raise ConnectionError(
                    f"Failed to ping DB API '{self.base_url}/health'. "
                    f"HTTP status code: {resp.status}"
                )

    def info(self, message, thing_uuid):
        self._to_journal("INFO", message, thing_uuid)

    def warning(self, message, thing_uuid):
        self._to_journal("WARNING", message, thing_uuid)

    def error(self, message, thing_uuid):
        self._to_journal("ERROR", message, thing_uuid)

    def _to_journal(self, level: str, message: str, thing_uuid):
        if not self.enabled:
            return
        data = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "message": message,
            "level": level,
            "origin": self.name,
        }
        logger.info("Message to journal:\n>> %s[%s]: %s", self.name, level, message)

        req = request.Request(
            url=f"{self.base_url}/journal/{thing_uuid}",
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        logger.debug(f"%s %s, data: %s", req.method, req.full_url, req.data)

        try:
            resp: HTTPResponse = request.urlopen(req)
            logger.debug("==> %s, %s", resp.status, resp.reason)

        except Exception as e:
            if isinstance(e, HTTPError):
                # HttpError is also an HTTPResponse object
                logger.debug("==> %s, %s, %s", e.status, e.reason, e.read().decode())
            if self.error_strategy == "raise":
                raise RuntimeError("Storing message to journal failed") from e
            if self.error_strategy == "warn":
                warnings.warn(
                    f"Storing message to journal failed, "
                    f"because of {type(e).__name__}: {e}",
                    RuntimeWarning,
                    stacklevel=3,
                )
