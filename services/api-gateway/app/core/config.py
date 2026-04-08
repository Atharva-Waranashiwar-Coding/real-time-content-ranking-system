"""Configuration for api-gateway."""

from shared_config import settings as base_settings


class ServiceConfig:
    """Service-specific configuration."""

    SERVICE_NAME = "api-gateway"
    SERVICE_PORT = 8000

    DEBUG = base_settings.DEBUG
    LOG_LEVEL = base_settings.LOG_LEVEL
    DATABASE_URL = base_settings.database_url
    REDIS_URL = base_settings.redis_url
    KAFKA_BOOTSTRAP_SERVERS = base_settings.KAFKA_BOOTSTRAP_SERVERS
    REQUEST_ID_HEADER = "X-Request-ID"
    CORRELATION_ID_HEADER = "X-Correlation-ID"


config = ServiceConfig()
