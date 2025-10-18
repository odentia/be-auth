from __future__ import annotations

import logging
import os
from typing import Any

from rich.console import Console
from rich.logging import RichHandler

_INITIALIZED = False
_console = Console()


def init_logging(level: str = "INFO") -> None:

    global _INITIALIZED
    if _INITIALIZED:
        return

    level_num = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        level=level_num,
        format="%(message)s",  # RichHandler renders time/level/name
        datefmt="[%X]",
        handlers=[RichHandler(console=_console, markup=True, rich_tracebacks=True)],
    )

    for noisy in ("uvicorn.access", "asyncio", "aiosqlite"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    if os.getenv("LOG_SQLALCHEMY_DEBUG") == "1":
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

    _INITIALIZED = True


def get_logger(name: str) -> logging.Logger:

    return logging.getLogger(name)

def set_level(level: str) -> None:

    lvl = getattr(logging, level.upper(), logging.INFO)
    logging.getLogger().setLevel(lvl)


def bind(logger: logging.Logger, **extra: Any) -> logging.LoggerAdapter:

    return logging.LoggerAdapter(logger, extra=extra)
