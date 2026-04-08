"""Redis-backed materialization store for feature-processor."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from app.services.aggregation import (
    METRIC_FIELDS,
    ContentFeatureRecord,
    MetricCounts,
    UserTopicAffinityRecord,
    build_content_feature_record,
    build_user_topic_affinity_record,
    metric_field_for_event_type,
)

from shared_schemas import InteractionEventV1Schema, utc_now


class RedisClientProtocol(Protocol):
    """Minimal Redis API used by the feature store."""

    async def expire(self, name: str, time: int) -> bool:
        """Set a TTL on the given key."""

    async def hget(self, name: str, key: str) -> str | None:
        """Get a single hash field."""

    async def hgetall(self, name: str) -> dict[str, str]:
        """Get all hash fields."""

    async def hset(self, name: str, mapping: dict[str, object]) -> int:
        """Set one or more hash fields."""

    async def ping(self) -> bool:
        """Ping Redis."""

    async def zadd(self, name: str, mapping: dict[str, float]) -> int:
        """Add sorted-set members."""

    async def zcard(self, name: str) -> int:
        """Count sorted-set members."""

    async def zremrangebyscore(self, name: str, min: float, max: float) -> int:
        """Remove sorted-set members in a score range."""


class RedisFeatureStore:
    """Read/write low-latency feature materializations in Redis."""

    def __init__(self, redis_client: RedisClientProtocol, window_hours: int):
        self.redis = redis_client
        self.window_hours = window_hours
        self.window_seconds = window_hours * 3600
        self.metric_ttl_seconds = self.window_seconds * 2

    @staticmethod
    def content_feature_key(content_id: str) -> str:
        """Return the Redis hash key for a content feature vector."""

        return f"feature:content:{content_id}:v1"

    @staticmethod
    def content_metric_key(content_id: str, metric_name: str) -> str:
        """Return the Redis sorted-set key for a content rolling metric."""

        return f"feature:content:{content_id}:metric:{metric_name}:rolling-window:v1"

    @staticmethod
    def user_topic_affinity_key(user_id: str) -> str:
        """Return the Redis hash key for per-user topic affinity."""

        return f"feature:user:{user_id}:topic-affinity:v1"

    @staticmethod
    def user_topic_metric_key(user_id: str, topic: str, metric_name: str) -> str:
        """Return the Redis sorted-set key for a user-topic rolling metric."""

        return (
            "feature:user:"
            f"{user_id}:topic:{topic}:metric:{metric_name}:rolling-window:v1"
        )

    async def ping(self) -> bool:
        """Check Redis availability."""

        return bool(await self.redis.ping())

    async def update_content_feature(
        self,
        event: InteractionEventV1Schema,
        updated_at: datetime | None = None,
    ) -> ContentFeatureRecord:
        """Apply an interaction event to content-level rolling metrics."""

        metric_name = metric_field_for_event_type(event.event_type)
        content_id = str(event.content_id)
        await self._record_metric_event(
            key=self.content_metric_key(content_id, metric_name),
            event_id=str(event.event_id),
            event_timestamp=event.event_timestamp,
        )

        counts = await self._read_content_counts(content_id)
        counts.last_event_at = await self._coalesce_last_event_at(
            self.content_feature_key(content_id),
            event.event_timestamp,
        )
        topic = event.topic or await self.redis.hget(
            self.content_feature_key(content_id),
            "topic",
        )

        return build_content_feature_record(
            content_id=content_id,
            topic=topic,
            counts=counts,
            window_hours=self.window_hours,
            updated_at=updated_at or utc_now(),
        )

    async def write_content_feature(self, feature: ContentFeatureRecord) -> None:
        """Materialize the content feature vector as a Redis hash."""

        payload = feature.to_shared_schema().model_dump(mode="json")
        await self.redis.hset(self.content_feature_key(feature.content_id), mapping=payload)

    async def update_user_topic_affinity(
        self,
        event: InteractionEventV1Schema,
        updated_at: datetime | None = None,
    ) -> UserTopicAffinityRecord | None:
        """Apply an interaction event to per-user topic affinity metrics."""

        if event.topic is None:
            return None

        metric_name = metric_field_for_event_type(event.event_type)
        user_id = str(event.user_id)
        await self._record_metric_event(
            key=self.user_topic_metric_key(user_id, event.topic, metric_name),
            event_id=str(event.event_id),
            event_timestamp=event.event_timestamp,
        )

        counts = await self._read_user_topic_counts(user_id, event.topic)
        counts.last_event_at = await self._coalesce_last_event_at(
            self.user_topic_affinity_key(user_id),
            event.event_timestamp,
        )

        return build_user_topic_affinity_record(
            user_id=user_id,
            topic=event.topic,
            counts=counts,
            window_hours=self.window_hours,
            updated_at=updated_at or utc_now(),
        )

    async def write_user_topic_affinity(self, feature: UserTopicAffinityRecord) -> None:
        """Materialize the user affinity vector as a Redis hash."""

        affinity_map = await self.read_user_topic_affinity_map(feature.user_id)
        affinity_map[feature.topic] = feature.affinity_score
        payload = feature.to_shared_schema(affinity_map).model_dump(mode="json")

        flattened_mapping: dict[str, object] = {
            "schema_name": payload["schema_name"],
            "user_id": payload["user_id"],
            "window_hours": payload["window_hours"],
            "last_event_at": payload["last_event_at"] or "",
            "updated_at": payload["updated_at"],
        }
        for topic, affinity_score in payload["topic_affinity"].items():
            flattened_mapping[f"topic_affinity.{topic}"] = affinity_score

        await self.redis.hset(self.user_topic_affinity_key(feature.user_id), mapping=flattened_mapping)

    async def read_user_topic_affinity_map(self, user_id: str) -> dict[str, float]:
        """Return the stored user affinity map from Redis."""

        values = await self.redis.hgetall(self.user_topic_affinity_key(user_id))
        affinity_map: dict[str, float] = {}
        for field_name, raw_value in values.items():
            if field_name.startswith("topic_affinity.") and raw_value != "":
                topic = field_name.removeprefix("topic_affinity.")
                affinity_map[topic] = float(raw_value)
        return affinity_map

    async def _record_metric_event(
        self,
        key: str,
        event_id: str,
        event_timestamp: datetime,
    ) -> None:
        """Store a rolling metric event in Redis and prune expired members."""

        event_score = event_timestamp.timestamp()
        window_start = event_score - self.window_seconds
        await self.redis.zadd(key, {event_id: event_score})
        await self.redis.zremrangebyscore(key, 0, window_start)
        await self.redis.expire(key, self.metric_ttl_seconds)

    async def _read_content_counts(self, content_id: str) -> MetricCounts:
        """Read rolling content metric counts from Redis."""

        return await self._read_metric_counts(
            lambda metric_name: self.content_metric_key(content_id, metric_name)
        )

    async def _read_user_topic_counts(self, user_id: str, topic: str) -> MetricCounts:
        """Read rolling user-topic metric counts from Redis."""

        return await self._read_metric_counts(
            lambda metric_name: self.user_topic_metric_key(user_id, topic, metric_name)
        )

    async def _read_metric_counts(self, key_builder) -> MetricCounts:
        """Read metric counts for the provided Redis key builder."""

        counts = MetricCounts()
        for metric_name in METRIC_FIELDS:
            count = await self.redis.zcard(key_builder(metric_name))
            setattr(counts, metric_name, int(count))
        return counts

    async def _coalesce_last_event_at(
        self,
        hash_key: str,
        candidate: datetime,
    ) -> datetime:
        """Keep the most recent event timestamp when events arrive out of order."""

        existing_raw_value = await self.redis.hget(hash_key, "last_event_at")
        if not existing_raw_value:
            return candidate

        existing_timestamp = datetime.fromisoformat(existing_raw_value)
        return max(existing_timestamp, candidate)


__all__ = ["RedisClientProtocol", "RedisFeatureStore"]
