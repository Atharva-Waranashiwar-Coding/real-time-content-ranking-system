"""Shared logging and observability utilities."""

from __future__ import annotations

import logging
import sys
from datetime import timezone
from typing import Any

from pythonjsonlogger import jsonlogger

from shared_schemas import utc_now

from .health import (
    build_health_response,
    check_database_session_factory,
    check_redis_client,
)
from .http import DEFAULT_QUIET_PATHS, install_http_observability
from .metrics import (
    build_metrics_router,
    observe_consumer_lag,
    observe_dependency_request,
    observe_event_operation,
    observe_feed_assembly_duration,
    observe_ranking_duration,
    record_retry_attempt,
    render_prometheus_metrics,
)


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for structured logging."""

    def __init__(self, service_name: str):
        super().__init__("%(message)s")
        self.service_name = service_name

    def add_fields(
        self,
        log_record: dict[str, Any],
        record: logging.LogRecord,
        message_dict: dict[str, Any],
    ) -> None:
        """Add consistent service metadata to every log record."""

        super().add_fields(log_record, record, message_dict)
        log_record["timestamp"] = utc_now().astimezone(timezone.utc).isoformat()
        log_record["level"] = record.levelname
        log_record["logger_name"] = record.name
        log_record.setdefault("service_name", self.service_name)
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)


def setup_logging(service_name: str, log_level: str = "INFO") -> logging.Logger:
    """Set up structured JSON logging for a service."""

    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.propagate = False

    if any(getattr(handler, "_content_ranking_handler", False) for handler in logger.handlers):
        return logger

    handler = logging.StreamHandler(sys.stdout)
    handler._content_ranking_handler = True  # type: ignore[attr-defined]
    handler.setFormatter(CustomJsonFormatter(service_name=service_name))
    logger.handlers.clear()
    logger.addHandler(handler)
    return logger


__all__ = [
    "DEFAULT_QUIET_PATHS",
    "CustomJsonFormatter",
    "build_health_response",
    "build_metrics_router",
    "check_database_session_factory",
    "check_redis_client",
    "install_http_observability",
    "observe_consumer_lag",
    "observe_dependency_request",
    "observe_event_operation",
    "observe_feed_assembly_duration",
    "observe_ranking_duration",
    "record_retry_attempt",
    "render_prometheus_metrics",
    "setup_logging",
]
