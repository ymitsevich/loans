"""Logging helpers for consistent, structured logs."""

from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any, Dict

_LEVEL_NAMES: Dict[str, int] = {
    "critical": logging.CRITICAL,
    "error": logging.ERROR,
    "warning": logging.WARNING,
    "info": logging.INFO,
    "debug": logging.DEBUG,
    "trace": 5,  # optional custom level if desired
}


class JsonFormatter(logging.Formatter):
    """Render log records as JSON for easier ingestion."""

    default_time_format = "%Y-%m-%dT%H:%M:%S"
    default_msec_format = "%s.%03d"

    def format(self, record: logging.LogRecord) -> str:
        log = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
        }
        extra = getattr(record, "extra_data", None)
        if isinstance(extra, dict):
            log.update(extra)
        if record.exc_info:
            log["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log, default=str)


def configure_logging(level: str | None = None) -> None:
    """Configure root logging to emit JSON messages to stdout."""
    resolved_level = _LEVEL_NAMES.get((level or os.getenv("LOG_LEVEL", "info")).lower(), logging.INFO)
    root = logging.getLogger()
    logging.captureWarnings(True)

    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        root.addHandler(handler)
    else:
        for handler in root.handlers:
            handler.setFormatter(JsonFormatter())

    root.setLevel(resolved_level)
