"""Configuration for feature-processor."""

import os

from shared_config import settings as base_settings
from shared_schemas import (
    DEFAULT_FEATURE_WINDOW_HOURS,
    INTERACTIONS_EVENTS_DLQ_V1_TOPIC,
    INTERACTIONS_EVENTS_V1_TOPIC,
)


class ServiceConfig:
    """Service-specific configuration."""

    SERVICE_NAME = "feature-processor"
    SERVICE_PORT = 8008

    DEBUG = base_settings.DEBUG
    LOG_LEVEL = base_settings.LOG_LEVEL
    DATABASE_URL = base_settings.database_url
    REDIS_URL = base_settings.redis_url
    KAFKA_BOOTSTRAP_SERVERS = base_settings.KAFKA_BOOTSTRAP_SERVERS
    KAFKA_INTERACTIONS_TOPIC = INTERACTIONS_EVENTS_V1_TOPIC
    KAFKA_CONSUMER_GROUP = os.getenv(
        "KAFKA_CONSUMER_GROUP",
        "feature-processor-v1",
    )
    KAFKA_AUTO_OFFSET_RESET = os.getenv("KAFKA_AUTO_OFFSET_RESET", "latest")
    KAFKA_POLL_TIMEOUT_SECONDS = float(os.getenv("KAFKA_POLL_TIMEOUT_SECONDS", "1"))
    KAFKA_DLQ_TOPIC = os.getenv(
        "KAFKA_DLQ_TOPIC",
        INTERACTIONS_EVENTS_DLQ_V1_TOPIC,
    )
    FEATURE_WINDOW_HOURS = int(
        os.getenv("FEATURE_WINDOW_HOURS", str(DEFAULT_FEATURE_WINDOW_HOURS))
    )
    FEATURE_SNAPSHOT_FLUSH_INTERVAL_SECONDS = float(
        os.getenv("FEATURE_SNAPSHOT_FLUSH_INTERVAL_SECONDS", "15")
    )
    FEATURE_SNAPSHOT_BATCH_SIZE = int(
        os.getenv("FEATURE_SNAPSHOT_BATCH_SIZE", "25")
    )
    FEATURE_PROCESSOR_START_CONSUMER = (
        os.getenv("FEATURE_PROCESSOR_START_CONSUMER", "true").lower() == "true"
    )
    PROCESSOR_ERROR_BACKOFF_SECONDS = float(
        os.getenv("PROCESSOR_ERROR_BACKOFF_SECONDS", "1")
    )
    PROCESSOR_MAX_PROCESSING_ATTEMPTS = int(
        os.getenv("PROCESSOR_MAX_PROCESSING_ATTEMPTS", "3")
    )
    REQUEST_ID_HEADER = "X-Request-ID"
    CORRELATION_ID_HEADER = "X-Correlation-ID"


config = ServiceConfig()
