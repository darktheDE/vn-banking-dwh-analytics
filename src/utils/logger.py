"""Logging configuration for all batch jobs.

Provides get_logger(name) factory function.
Standard format: timestamp | level | module | message
"""

import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger instance for the given module name.

    Uses a standard format with timestamp, log level, and module name.
    Logs are written to stdout so they can be captured by any orchestration
    layer without requiring file-based handlers.

    Args:
        name: The module name, typically passed as __name__.

    Returns:
        A logging.Logger configured with the project-standard format.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger
