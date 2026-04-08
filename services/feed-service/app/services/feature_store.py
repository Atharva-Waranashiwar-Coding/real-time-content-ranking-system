"""Redis-backed feature and cache access for feed-service."""

from __future__ import annotations

import json
from typing import Protocol

from shared_schemas import ContentFeaturesV1Schema, utc_now


class RedisClientProtocol(Protocol):
    """Minimal Redis API used by feed-service."""

    async def aclose(self) -> None:
        """Close Redis resources."""

    async def expire(self, name: str, time: int) -> bool:
        """Set a TTL on a key."""

    async def get(self, name: str) -> str | None:
        """Get a string value."""

    async def hgetall(self, name: str) -> dict[str, str]:
        """Read all fields from a hash."""

    async def hset(self, name: str, mapping: dict[str, object]) -> int:
        """Write one or more hash fields."""

    async def ping(self) -> bool:
        """Ping Redis."""

    async def set(self, name: str, value: str, ex: int | None = None) -> bool:
        """Set a string value with an optional TTL."""


class FeedRedisStore:
    """Read feature-processor materializations and cache feed responses."""

    def __init__(self, redis_client: RedisClientProtocol):
        self.redis = redis_client

    @staticmethod
    def content_feature_key(content_id: str) -> str:
        """Return the Redis hash key for a content feature vector."""

        return f"feature:content:{content_id}:v1"

    @staticmethod
    def user_topic_affinity_key(user_id: str) -> str:
        """Return the Redis hash key for a user topic affinity vector."""

        return f"feature:user:{user_id}:topic-affinity:v1"

    @staticmethod
    def feed_cache_key(
        user_id: str,
        experiment_key: str,
        variant_key: str,
        limit: int,
        offset: int,
    ) -> str:
        """Return the Redis cache key for a paginated feed response."""

        return (
            f"feed:user:{user_id}:experiment:{experiment_key}:variant:{variant_key}:"
            f"limit:{limit}:offset:{offset}:v1"
        )

    async def ping(self) -> bool:
        """Check Redis availability."""

        return bool(await self.redis.ping())

    async def read_content_features(
        self,
        content_id: str,
        *,
        topic: str | None = None,
    ) -> ContentFeaturesV1Schema:
        """Read content features from Redis or return an empty default vector."""

        raw_fields = await self.redis.hgetall(self.content_feature_key(content_id))
        if not raw_fields:
            return ContentFeaturesV1Schema(content_id=content_id, topic=topic)

        payload = {
            "content_id": content_id,
            "topic": raw_fields.get("topic") or topic,
            "window_hours": int(raw_fields.get("window_hours", 24)),
            "impressions": int(raw_fields.get("impressions", 0)),
            "clicks": int(raw_fields.get("clicks", 0)),
            "likes": int(raw_fields.get("likes", 0)),
            "saves": int(raw_fields.get("saves", 0)),
            "skip_count": int(raw_fields.get("skip_count", 0)),
            "watch_starts": int(raw_fields.get("watch_starts", 0)),
            "watch_completes": int(raw_fields.get("watch_completes", 0)),
            "ctr": float(raw_fields.get("ctr", 0.0)),
            "like_rate": float(raw_fields.get("like_rate", 0.0)),
            "save_rate": float(raw_fields.get("save_rate", 0.0)),
            "skip_rate": float(raw_fields.get("skip_rate", 0.0)),
            "completion_rate": float(raw_fields.get("completion_rate", 0.0)),
            "trending_score": float(raw_fields.get("trending_score", 0.0)),
            "last_event_at": raw_fields.get("last_event_at") or None,
            "updated_at": raw_fields.get("updated_at") or utc_now(),
        }
        return ContentFeaturesV1Schema.model_validate(payload)

    async def read_user_topic_affinity(self, user_id: str) -> dict[str, float]:
        """Read the latest user topic affinity vector from Redis."""

        raw_fields = await self.redis.hgetall(self.user_topic_affinity_key(user_id))
        topic_affinity: dict[str, float] = {}
        for field_name, raw_value in raw_fields.items():
            if field_name.startswith("topic_affinity.") and raw_value != "":
                topic = field_name.removeprefix("topic_affinity.")
                topic_affinity[topic] = float(raw_value)
        return topic_affinity

    async def get_cached_feed(
        self,
        user_id: str,
        experiment_key: str,
        variant_key: str,
        limit: int,
        offset: int,
    ) -> dict | None:
        """Return a cached feed payload if one exists."""

        raw_payload = await self.redis.get(
            self.feed_cache_key(user_id, experiment_key, variant_key, limit, offset)
        )
        if raw_payload is None:
            return None
        return json.loads(raw_payload)

    async def set_cached_feed(
        self,
        user_id: str,
        experiment_key: str,
        variant_key: str,
        limit: int,
        offset: int,
        payload: dict,
        ttl_seconds: int,
    ) -> None:
        """Cache a paginated feed response."""

        await self.redis.set(
            self.feed_cache_key(user_id, experiment_key, variant_key, limit, offset),
            json.dumps(payload, separators=(",", ":"), sort_keys=True),
            ex=ttl_seconds,
        )
