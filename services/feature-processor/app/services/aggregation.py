"""Deterministic aggregation logic for feature-processor."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import exp

from shared_schemas import (
    CONTENT_FEATURES_V1_SCHEMA_NAME,
    USER_TOPIC_AFFINITY_V1_SCHEMA_NAME,
    ContentFeaturesV1Schema,
    InteractionEventType,
    UserTopicAffinityV1Schema,
    utc_now,
)

EVENT_TYPE_TO_METRIC_FIELD = {
    InteractionEventType.IMPRESSION: "impressions",
    InteractionEventType.CLICK: "clicks",
    InteractionEventType.LIKE: "likes",
    InteractionEventType.SAVE: "saves",
    InteractionEventType.SKIP: "skip_count",
    InteractionEventType.WATCH_START: "watch_starts",
    InteractionEventType.WATCH_COMPLETE: "watch_completes",
}
METRIC_FIELDS = tuple(EVENT_TYPE_TO_METRIC_FIELD.values())
TRENDING_EVENT_WEIGHTS = {
    "impressions": 0.1,
    "clicks": 1.0,
    "likes": 3.0,
    "saves": 4.0,
    "skip_count": -2.5,
    "watch_starts": 0.75,
    "watch_completes": 3.5,
}
TOPIC_AFFINITY_WEIGHTS = {
    "impressions": 0.2,
    "clicks": 1.5,
    "likes": 4.0,
    "saves": 5.0,
    "skip_count": -3.0,
    "watch_starts": 1.0,
    "watch_completes": 4.5,
}


@dataclass(slots=True)
class MetricCounts:
    """Rolling event counts used for content and user-topic aggregates."""

    impressions: int = 0
    clicks: int = 0
    likes: int = 0
    saves: int = 0
    skip_count: int = 0
    watch_starts: int = 0
    watch_completes: int = 0
    last_event_at: datetime | None = None


@dataclass(slots=True)
class ContentFeatureRecord:
    """Materialized content feature vector and snapshot payload."""

    content_id: str
    window_hours: int
    impressions: int
    clicks: int
    likes: int
    saves: int
    skip_count: int
    watch_starts: int
    watch_completes: int
    ctr: float
    like_rate: float
    save_rate: float
    skip_rate: float
    completion_rate: float
    trending_score: float
    topic: str | None
    last_event_at: datetime | None
    updated_at: datetime
    schema_name: str = CONTENT_FEATURES_V1_SCHEMA_NAME

    def to_shared_schema(self) -> ContentFeaturesV1Schema:
        """Convert to the shared content feature schema."""

        return ContentFeaturesV1Schema(
            schema_name=self.schema_name,
            content_id=self.content_id,
            topic=self.topic,
            window_hours=self.window_hours,
            impressions=self.impressions,
            clicks=self.clicks,
            likes=self.likes,
            saves=self.saves,
            skip_count=self.skip_count,
            watch_starts=self.watch_starts,
            watch_completes=self.watch_completes,
            ctr=self.ctr,
            like_rate=self.like_rate,
            save_rate=self.save_rate,
            skip_rate=self.skip_rate,
            completion_rate=self.completion_rate,
            trending_score=self.trending_score,
            last_event_at=self.last_event_at,
            updated_at=self.updated_at,
        )


@dataclass(slots=True)
class UserTopicAffinityRecord:
    """Materialized per-user topic affinity vector and snapshot payload."""

    user_id: str
    topic: str
    window_hours: int
    impressions: int
    clicks: int
    likes: int
    saves: int
    skip_count: int
    watch_starts: int
    watch_completes: int
    affinity_score: float
    last_event_at: datetime | None
    updated_at: datetime
    schema_name: str = USER_TOPIC_AFFINITY_V1_SCHEMA_NAME

    def to_shared_schema(
        self,
        topic_affinity: dict[str, float],
    ) -> UserTopicAffinityV1Schema:
        """Convert to the shared user affinity schema."""

        return UserTopicAffinityV1Schema(
            schema_name=self.schema_name,
            user_id=self.user_id,
            window_hours=self.window_hours,
            topic_affinity=topic_affinity,
            last_event_at=self.last_event_at,
            updated_at=self.updated_at,
        )


def metric_field_for_event_type(event_type: InteractionEventType) -> str:
    """Return the stored metric field name for an interaction type."""

    return EVENT_TYPE_TO_METRIC_FIELD[event_type]


def compute_rate(numerator: int, denominator: int) -> float:
    """Safely compute a bounded ratio."""

    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 6)


def compute_trending_score(
    counts: MetricCounts,
    window_hours: int,
    now: datetime | None = None,
) -> float:
    """Compute a deterministic, recency-aware trending score."""

    current_time = now or utc_now()
    weighted_total = sum(
        getattr(counts, metric_name) * weight
        for metric_name, weight in TRENDING_EVENT_WEIGHTS.items()
    )
    quality_bonus = (
        compute_rate(counts.clicks, counts.impressions) * 10.0
        + compute_rate(counts.likes, max(counts.clicks, 1)) * 6.0
        + compute_rate(counts.saves, max(counts.clicks, 1)) * 8.0
        + compute_rate(counts.watch_completes, max(counts.watch_starts, 1)) * 12.0
    )
    raw_score = max(weighted_total + quality_bonus, 0.0)

    if counts.last_event_at is None:
        return round(raw_score, 6)

    age_seconds = max(
        (current_time - counts.last_event_at).total_seconds(),
        0.0,
    )
    decay = exp(-age_seconds / max(window_hours * 3600, 1))
    return round(raw_score * decay, 6)


def compute_topic_affinity_score(counts: MetricCounts) -> float:
    """Compute a weighted topic affinity score."""

    weighted_total = sum(
        getattr(counts, metric_name) * weight
        for metric_name, weight in TOPIC_AFFINITY_WEIGHTS.items()
    )
    completion_bonus = compute_rate(counts.watch_completes, max(counts.watch_starts, 1)) * 5.0
    return round(weighted_total + completion_bonus, 6)


def build_content_feature_record(
    content_id: str,
    topic: str | None,
    counts: MetricCounts,
    window_hours: int,
    updated_at: datetime | None = None,
) -> ContentFeatureRecord:
    """Build the materialized content feature vector from rolling counts."""

    current_time = updated_at or utc_now()
    return ContentFeatureRecord(
        content_id=content_id,
        topic=topic,
        window_hours=window_hours,
        impressions=counts.impressions,
        clicks=counts.clicks,
        likes=counts.likes,
        saves=counts.saves,
        skip_count=counts.skip_count,
        watch_starts=counts.watch_starts,
        watch_completes=counts.watch_completes,
        ctr=compute_rate(counts.clicks, counts.impressions),
        like_rate=compute_rate(counts.likes, counts.clicks),
        save_rate=compute_rate(counts.saves, counts.clicks),
        skip_rate=compute_rate(counts.skip_count, counts.impressions),
        completion_rate=compute_rate(counts.watch_completes, counts.watch_starts),
        trending_score=compute_trending_score(counts, window_hours, current_time),
        last_event_at=counts.last_event_at,
        updated_at=current_time,
    )


def build_user_topic_affinity_record(
    user_id: str,
    topic: str,
    counts: MetricCounts,
    window_hours: int,
    updated_at: datetime | None = None,
) -> UserTopicAffinityRecord:
    """Build the materialized topic affinity feature from rolling counts."""

    current_time = updated_at or utc_now()
    return UserTopicAffinityRecord(
        user_id=user_id,
        topic=topic,
        window_hours=window_hours,
        impressions=counts.impressions,
        clicks=counts.clicks,
        likes=counts.likes,
        saves=counts.saves,
        skip_count=counts.skip_count,
        watch_starts=counts.watch_starts,
        watch_completes=counts.watch_completes,
        affinity_score=compute_topic_affinity_score(counts),
        last_event_at=counts.last_event_at,
        updated_at=current_time,
    )


__all__ = [
    "ContentFeatureRecord",
    "EVENT_TYPE_TO_METRIC_FIELD",
    "METRIC_FIELDS",
    "MetricCounts",
    "TOPIC_AFFINITY_WEIGHTS",
    "TRENDING_EVENT_WEIGHTS",
    "UserTopicAffinityRecord",
    "build_content_feature_record",
    "build_user_topic_affinity_record",
    "compute_rate",
    "compute_topic_affinity_score",
    "compute_trending_score",
    "metric_field_for_event_type",
]
