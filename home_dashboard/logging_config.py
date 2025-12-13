"""Structured logging configuration for Home Dashboard.

This module configures JSON structured logging to file and human-readable console logging.
Logs are written to logs/dashboard.log with 10MB rotation and 5 backups.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from pythonjsonlogger import jsonlogger


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configure structured logging with JSON file output and console output.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured root logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove any existing handlers
    root_logger.handlers.clear()

    # JSON file handler with rotation (10MB, 5 backups)
    json_handler = RotatingFileHandler(
        log_dir / "dashboard.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    json_formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s %(filename)s %(lineno)d",
        timestamp=True,
    )
    json_handler.setFormatter(json_formatter)
    json_handler.setLevel(logging.DEBUG)  # Capture all levels to file
    root_logger.addHandler(json_handler)

    # Console handler with human-readable format
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    root_logger.addHandler(console_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with structured logging support.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance configured for structured logging
    """
    return logging.getLogger(name)


def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    **extra_fields: Any,
) -> None:
    """Log a message with additional structured context fields.

    Args:
        logger: Logger instance
        level: Log level (debug, info, warning, error, critical)
        message: Log message
        **extra_fields: Additional fields to include in JSON log (e.g., user_id, request_id)
    """
    log_method = getattr(logger, level.lower())
    log_method(message, extra=extra_fields)
