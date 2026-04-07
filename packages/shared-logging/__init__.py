"""Shared logging utilities for the real-time content ranking system."""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict
from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for structured logging."""

    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """Add custom fields to log record."""
        super().add_fields(log_record, record, message_dict)
        log_record["timestamp"] = datetime.utcnow().isoformat()
        log_record["level"] = record.levelname
        log_record["logger_name"] = record.name
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)


def setup_logging(service_name: str, log_level: str = "INFO") -> logging.Logger:
    """Set up structured logging for a service.
    
    Args:
        service_name: Name of the service for logging context
        log_level: Logging level (INFO, DEBUG, WARNING, ERROR)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, log_level.upper()))

    # JSON formatter handler
    handler = logging.StreamHandler(sys.stdout)
    formatter = CustomJsonFormatter("%(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


__all__ = ["setup_logging", "CustomJsonFormatter"]
