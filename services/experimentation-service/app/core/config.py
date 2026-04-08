"""Configuration for experimentation-service."""

import os

from shared_config import settings as base_settings
from shared_schemas import HOME_FEED_RANKING_EXPERIMENT_KEY


class ServiceConfig:
    """Service-specific configuration."""

    SERVICE_NAME = "experimentation-service"
    SERVICE_PORT = 8006

    DEBUG = base_settings.DEBUG
    LOG_LEVEL = base_settings.LOG_LEVEL
    DATABASE_URL = base_settings.database_url
    REDIS_URL = base_settings.redis_url
    KAFKA_BOOTSTRAP_SERVERS = base_settings.KAFKA_BOOTSTRAP_SERVERS
    REQUEST_ID_HEADER = "X-Request-ID"
    CORRELATION_ID_HEADER = "X-Correlation-ID"
    ACTIVE_EXPERIMENT_KEY = os.getenv(
        "ACTIVE_EXPERIMENT_KEY",
        HOME_FEED_RANKING_EXPERIMENT_KEY,
    )


config = ServiceConfig()
