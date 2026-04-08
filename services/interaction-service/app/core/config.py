"""Configuration for interaction-service."""

import os

from shared_config import settings as base_settings
from shared_schemas import INTERACTIONS_EVENTS_V1_TOPIC


class ServiceConfig:
    """Service-specific configuration."""

    SERVICE_NAME = "interaction-service"
    SERVICE_PORT = 8003

    DEBUG = base_settings.DEBUG
    LOG_LEVEL = base_settings.LOG_LEVEL
    DATABASE_URL = base_settings.database_url
    REDIS_URL = base_settings.redis_url
    KAFKA_BOOTSTRAP_SERVERS = base_settings.KAFKA_BOOTSTRAP_SERVERS
    KAFKA_INTERACTIONS_TOPIC = INTERACTIONS_EVENTS_V1_TOPIC
    KAFKA_PUBLISH_TIMEOUT_SECONDS = float(os.getenv("KAFKA_PUBLISH_TIMEOUT_SECONDS", "5"))
    REQUEST_ID_HEADER = "X-Request-ID"
    CORRELATION_ID_HEADER = "X-Correlation-ID"


config = ServiceConfig()
