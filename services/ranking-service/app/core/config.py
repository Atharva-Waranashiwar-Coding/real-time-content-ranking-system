"""Configuration for ranking-service."""

import os

from shared_config import settings as base_settings
from shared_schemas import RANKING_DECISIONS_V1_TOPIC, RULES_V1_RANKING_STRATEGY


class ServiceConfig:
    """Service-specific configuration."""

    SERVICE_NAME = "ranking-service"
    SERVICE_PORT = 8005

    DEBUG = base_settings.DEBUG
    LOG_LEVEL = base_settings.LOG_LEVEL
    DATABASE_URL = base_settings.database_url
    REDIS_URL = base_settings.redis_url
    KAFKA_BOOTSTRAP_SERVERS = base_settings.KAFKA_BOOTSTRAP_SERVERS
    KAFKA_RANKING_DECISIONS_TOPIC = RANKING_DECISIONS_V1_TOPIC
    DEFAULT_RANKING_STRATEGY = RULES_V1_RANKING_STRATEGY
    REQUEST_ID_HEADER = "X-Request-ID"
    CORRELATION_ID_HEADER = "X-Correlation-ID"
    USER_TOPIC_AFFINITY_WEIGHT = float(
        os.getenv("USER_TOPIC_AFFINITY_WEIGHT", "0.35")
    )
    RECENCY_WEIGHT = float(os.getenv("RECENCY_WEIGHT", "0.20"))
    ENGAGEMENT_WEIGHT = float(os.getenv("ENGAGEMENT_WEIGHT", "0.25"))
    TRENDING_WEIGHT = float(os.getenv("TRENDING_WEIGHT", "0.20"))
    DIVERSITY_TOPIC_PENALTY = float(
        os.getenv("DIVERSITY_TOPIC_PENALTY", "0.12")
    )
    DIVERSITY_CATEGORY_PENALTY = float(
        os.getenv("DIVERSITY_CATEGORY_PENALTY", "0.05")
    )
    MAX_DIVERSITY_PENALTY = float(os.getenv("MAX_DIVERSITY_PENALTY", "0.35"))
    RECENCY_HALFLIFE_HOURS = float(os.getenv("RECENCY_HALFLIFE_HOURS", "48"))
    TRENDING_SCORE_SATURATION = float(
        os.getenv("TRENDING_SCORE_SATURATION", "25")
    )
    V2_USER_TOPIC_AFFINITY_WEIGHT = float(
        os.getenv("V2_USER_TOPIC_AFFINITY_WEIGHT", "0.32")
    )
    V2_RECENCY_WEIGHT = float(os.getenv("V2_RECENCY_WEIGHT", "0.18"))
    V2_ENGAGEMENT_WEIGHT = float(os.getenv("V2_ENGAGEMENT_WEIGHT", "0.22"))
    V2_TRENDING_WEIGHT = float(os.getenv("V2_TRENDING_WEIGHT", "0.28"))
    V2_TRENDING_BOOST_THRESHOLD = float(
        os.getenv("V2_TRENDING_BOOST_THRESHOLD", "0.45")
    )
    V2_TRENDING_BOOST_MULTIPLIER = float(
        os.getenv("V2_TRENDING_BOOST_MULTIPLIER", "0.15")
    )
    V2_MAX_STRATEGY_ADJUSTMENT = float(
        os.getenv("V2_MAX_STRATEGY_ADJUSTMENT", "0.08")
    )


config = ServiceConfig()
