"""Configuration for feed-service."""

import os

from shared_config import settings as base_settings


class ServiceConfig:
    """Service-specific configuration."""

    SERVICE_NAME = "feed-service"
    SERVICE_PORT = 8004

    DEBUG = base_settings.DEBUG
    LOG_LEVEL = base_settings.LOG_LEVEL
    DATABASE_URL = base_settings.database_url
    REDIS_URL = base_settings.redis_url
    KAFKA_BOOTSTRAP_SERVERS = base_settings.KAFKA_BOOTSTRAP_SERVERS
    USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8001")
    CONTENT_SERVICE_URL = os.getenv("CONTENT_SERVICE_URL", "http://content-service:8002")
    RANKING_SERVICE_URL = os.getenv("RANKING_SERVICE_URL", "http://ranking-service:8005")
    REQUEST_ID_HEADER = "X-Request-ID"
    CORRELATION_ID_HEADER = "X-Correlation-ID"
    FEED_CACHE_TTL_SECONDS = int(os.getenv("FEED_CACHE_TTL_SECONDS", "60"))
    FEED_RECENT_CANDIDATE_LIMIT = int(
        os.getenv("FEED_RECENT_CANDIDATE_LIMIT", "40")
    )
    FEED_TRENDING_SEED_LIMIT = int(
        os.getenv("FEED_TRENDING_SEED_LIMIT", "100")
    )
    FEED_TRENDING_SOURCE_LIMIT = int(
        os.getenv("FEED_TRENDING_SOURCE_LIMIT", "20")
    )
    FEED_TOPIC_CANDIDATE_LIMIT = int(
        os.getenv("FEED_TOPIC_CANDIDATE_LIMIT", "20")
    )
    FEED_MAX_TOPIC_SOURCES = int(os.getenv("FEED_MAX_TOPIC_SOURCES", "3"))
    FEED_MAX_PAGE_SIZE = int(os.getenv("FEED_MAX_PAGE_SIZE", "100"))


config = ServiceConfig()
