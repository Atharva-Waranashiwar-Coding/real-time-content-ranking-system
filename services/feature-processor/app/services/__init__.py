"""Services for feature-processor."""

from app.services.aggregation import (
    ContentFeatureRecord,
    MetricCounts,
    UserTopicAffinityRecord,
    build_content_feature_record,
    build_user_topic_affinity_record,
    compute_topic_affinity_score,
    compute_trending_score,
)
from app.services.feature_processor import (
    EventProcessingContext,
    FeatureProcessorRuntimeState,
    FeatureProcessorService,
    FeatureSnapshotRepository,
    InvalidInteractionEventError,
)
from app.services.feature_store import RedisFeatureStore

__all__ = [
    "ContentFeatureRecord",
    "EventProcessingContext",
    "FeatureProcessorRuntimeState",
    "FeatureProcessorService",
    "FeatureSnapshotRepository",
    "InvalidInteractionEventError",
    "MetricCounts",
    "RedisFeatureStore",
    "UserTopicAffinityRecord",
    "build_content_feature_record",
    "build_user_topic_affinity_record",
    "compute_topic_affinity_score",
    "compute_trending_score",
]
