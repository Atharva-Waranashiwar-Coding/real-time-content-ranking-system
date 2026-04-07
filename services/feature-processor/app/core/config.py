"""Configuration for feature-processor."""

from shared_config import settings as base_settings


class ServiceConfig:
    """Service-specific configuration."""
    
    SERVICE_NAME = "feature-processor"
    SERVICE_PORT = 8008
    
    DEBUG = base_settings.DEBUG
    LOG_LEVEL = base_settings.LOG_LEVEL
    DATABASE_URL = base_settings.database_url
    REDIS_URL = base_settings.redis_url
    KAFKA_BOOTSTRAP_SERVERS = base_settings.KAFKA_BOOTSTRAP_SERVERS


config = ServiceConfig()
