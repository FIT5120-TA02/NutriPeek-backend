"""Logging configuration module."""

import logging
import sys
from typing import Any, Dict, Optional

from src.app.core.config import settings


def setup_logging() -> None:
    """Configure logging for the application."""
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Set log levels for third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DEBUG else logging.WARNING
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name.

    Returns:
        Logger instance.
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """Logger adapter with context information.

    This adapter adds context information to log messages.
    """

    def __init__(
        self, logger: logging.Logger, context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize LoggerAdapter.

        Args:
            logger: Logger instance.
            context: Context information.
        """
        super().__init__(logger, context or {})

    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """Process log message.

        Args:
            msg: Log message.
            kwargs: Keyword arguments.

        Returns:
            Processed message and keyword arguments.
        """
        context_str = " ".join(f"{k}={v}" for k, v in self.extra.items())
        return f"{msg} [{context_str}]", kwargs
