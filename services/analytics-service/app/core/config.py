"""Configuration for analytics-service."""

import os

from shared_config import settings as base_settings


class ServiceConfig:
    """Service-specific configuration."""

    SERVICE_NAME = "analytics-service"
    SERVICE_PORT = 8007

    DEBUG = base_settings.DEBUG
    LOG_LEVEL = base_settings.LOG_LEVEL
    DATABASE_URL = base_settings.database_url
    REDIS_URL = base_settings.redis_url
    KAFKA_BOOTSTRAP_SERVERS = base_settings.KAFKA_BOOTSTRAP_SERVERS
    REQUEST_ID_HEADER = "X-Request-ID"
    CORRELATION_ID_HEADER = "X-Correlation-ID"
    DEFAULT_EXPERIMENT_LOOKBACK_HOURS = int(
        os.getenv("DEFAULT_EXPERIMENT_LOOKBACK_HOURS", "168")
    )


config = ServiceConfig()
