"""
Centralised logging configuration.

Import and call ``setup_logging()`` once at programme startup.  Every module
should then simply use ``logging.getLogger(__name__)``.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from court_booker.config import ROOT_DIR

LOG_FILE = ROOT_DIR / "court_booking.log"


def setup_logging(level: int = logging.INFO) -> None:
    """Configure the root logger with file + stderr handlers."""
    fmt = "%(asctime)s — %(name)s — %(levelname)s — %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt, datefmt=datefmt)

    root = logging.getLogger()
    root.setLevel(level)

    # Avoid adding duplicate handlers if called more than once
    if root.handlers:
        return

    # File handler — persistent log
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    # Stderr handler — visible in cron error logs and during manual runs
    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)
