"""Feature processor runtime and snapshot persistence services."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from app.core.config import config
from app.core.metrics import (
    CONSUMER_RUNNING,
    EVENTS_FAILED_TOTAL,
    EVENTS_PROCESSED_TOTAL,
    LAST_PROCESSED_EVENT_UNIX,
    LAST_SNAPSHOT_FLUSH_UNIX,
    REDIS_MATERIALIZATIONS_TOTAL,
    SNAPSHOT_FLUSH_TOTAL,
)
from app.models import ContentFeatureSnapshot, UserTopicFeatureSnapshot
from app.schemas import ProcessorHealthResponse
from app.services.aggregation import ContentFeatureRecord, UserTopicAffinityRecord
from app.services.feature_store import RedisFeatureStore
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from shared_clients import KafkaConsumer, KafkaConsumerError, KafkaRecord
from shared_schemas import InteractionEventV1Schema, utc_now

logger = logging.getLogger(config.SERVICE_NAME)


class InvalidInteractionEventError(ValueError):
    """Raised when a consumed Kafka payload does not match the shared schema."""


@dataclass(slots=True)
class EventProcessingContext:
    """Identifiers and offsets attached to a consumed Kafka record."""

    request_id: str | None
    correlation_id: str | None
    kafka_topic: str
    kafka_partition: int | None
    kafka_offset: int | None

    @classmethod
    def from_record(cls, record: KafkaRecord) -> EventProcessingContext:
        """Build log context from a Kafka record."""

        return cls(
            request_id=record.headers.get("request-id") or None,
            correlation_id=record.headers.get("correlation-id") or None,
            kafka_topic=record.topic,
            kafka_partition=record.partition,
            kafka_offset=record.offset,
        )

    def to_log_fields(self) -> dict[str, str | int | None]:
        """Return structured log fields for event processing."""

        return {
            "request_id": self.request_id,
            "correlation_id": self.correlation_id,
            "kafka_topic": self.kafka_topic,
            "kafka_partition": self.kafka_partition,
            "kafka_offset": self.kafka_offset,
        }


@dataclass(slots=True)
class FeatureProcessorRuntimeState:
    """In-memory runtime state exposed via health endpoints."""

    service_name: str
    consumer_running: bool = False
    redis_available: bool = False
    database_available: bool = False
    last_processed_at: datetime | None = None
    last_snapshot_at: datetime | None = None
    processed_events_total: int = 0
    failed_events_total: int = 0
    dirty_content_feature_count: int = 0
    dirty_user_topic_feature_count: int = 0

    def to_response(self, status: str) -> ProcessorHealthResponse:
        """Convert the runtime state to a response payload."""

        return ProcessorHealthResponse(
            status=status,
            service=self.service_name,
            timestamp=utc_now(),
            consumer_running=self.consumer_running,
            redis_available=self.redis_available,
            database_available=self.database_available,
            last_processed_at=self.last_processed_at,
            last_snapshot_at=self.last_snapshot_at,
            processed_events_total=self.processed_events_total,
            failed_events_total=self.failed_events_total,
            dirty_content_feature_count=self.dirty_content_feature_count,
            dirty_user_topic_feature_count=self.dirty_user_topic_feature_count,
        )


class FeatureSnapshotRepository:
    """Persist periodic feature snapshots into PostgreSQL."""

    def __init__(self, session_factory: Callable[[], AsyncSession]):
        self.session_factory = session_factory

    async def ping(self) -> bool:
        """Check PostgreSQL availability."""

        async with self.session_factory() as session:
            result = await session.execute(text("SELECT 1"))
            return result.scalar_one() == 1

    async def write_snapshots(
        self,
        *,
        content_features: list[ContentFeatureRecord],
        user_topic_features: list[UserTopicAffinityRecord],
        snapshot_at: datetime,
    ) -> tuple[int, int]:
        """Persist a batch of content and user-topic feature snapshots."""

        async with self.session_factory() as session:
            session.add_all(
                [
                    ContentFeatureSnapshot(
                        schema_name=feature.schema_name,
                        content_id=feature.content_id,
                        topic=feature.topic,
                        window_hours=feature.window_hours,
                        impressions=feature.impressions,
                        clicks=feature.clicks,
                        likes=feature.likes,
                        saves=feature.saves,
                        skip_count=feature.skip_count,
                        watch_starts=feature.watch_starts,
                        watch_completes=feature.watch_completes,
                        ctr=feature.ctr,
                        like_rate=feature.like_rate,
                        save_rate=feature.save_rate,
                        skip_rate=feature.skip_rate,
                        completion_rate=feature.completion_rate,
                        trending_score=feature.trending_score,
                        last_event_at=feature.last_event_at,
                        snapshot_at=snapshot_at,
                    )
                    for feature in content_features
                ]
            )
            session.add_all(
                [
                    UserTopicFeatureSnapshot(
                        schema_name=feature.schema_name,
                        user_id=feature.user_id,
                        topic=feature.topic,
                        window_hours=feature.window_hours,
                        impressions=feature.impressions,
                        clicks=feature.clicks,
                        likes=feature.likes,
                        saves=feature.saves,
                        skip_count=feature.skip_count,
                        watch_starts=feature.watch_starts,
                        watch_completes=feature.watch_completes,
                        affinity_score=feature.affinity_score,
                        last_event_at=feature.last_event_at,
                        snapshot_at=snapshot_at,
                    )
                    for feature in user_topic_features
                ]
            )
            await session.commit()

        return len(content_features), len(user_topic_features)


class FeatureProcessorService:
    """Consume interaction events and materialize ranking features."""

    def __init__(
        self,
        *,
        feature_store: RedisFeatureStore,
        snapshot_repository: FeatureSnapshotRepository,
        runtime_state: FeatureProcessorRuntimeState | None = None,
        snapshot_batch_size: int,
        snapshot_flush_interval_seconds: float,
    ):
        self.feature_store = feature_store
        self.snapshot_repository = snapshot_repository
        self.runtime_state = runtime_state or FeatureProcessorRuntimeState(
            service_name=config.SERVICE_NAME
        )
        self.snapshot_batch_size = snapshot_batch_size
        self.snapshot_flush_interval_seconds = snapshot_flush_interval_seconds
        self._dirty_content_features: dict[str, ContentFeatureRecord] = {}
        self._dirty_user_topic_features: dict[tuple[str, str], UserTopicAffinityRecord] = {}
        self._last_snapshot_flush_attempt = utc_now()
        self._shutdown = asyncio.Event()
        self._flush_lock = asyncio.Lock()

    async def refresh_dependency_status(self) -> FeatureProcessorRuntimeState:
        """Refresh Redis and PostgreSQL availability for health checks."""

        self.runtime_state.redis_available = await self._check_redis()
        self.runtime_state.database_available = await self._check_database()
        self.runtime_state.dirty_content_feature_count = len(self._dirty_content_features)
        self.runtime_state.dirty_user_topic_feature_count = len(self._dirty_user_topic_features)
        return self.runtime_state

    async def run_forever(self, consumer: KafkaConsumer) -> None:
        """Continuously consume Kafka interaction events."""

        self.runtime_state.consumer_running = True
        CONSUMER_RUNNING.set(1)
        await self.refresh_dependency_status()

        try:
            while not self._shutdown.is_set():
                record = await consumer.poll(config.KAFKA_POLL_TIMEOUT_SECONDS)
                if record is None:
                    await self.maybe_flush_snapshots()
                    continue

                event_context = EventProcessingContext.from_record(record)
                should_commit = False
                try:
                    await self.process_record(record, event_context)
                    should_commit = True
                except InvalidInteractionEventError as exc:
                    should_commit = True
                    self.runtime_state.failed_events_total += 1
                    EVENTS_FAILED_TOTAL.inc()
                    logger.warning(
                        "Dropping invalid interaction event from Kafka",
                        extra={**event_context.to_log_fields(), "error": str(exc)},
                    )
                except Exception:
                    self.runtime_state.failed_events_total += 1
                    EVENTS_FAILED_TOTAL.inc()
                    logger.exception(
                        "Interaction feature processing failed",
                        extra=event_context.to_log_fields(),
                    )
                    await asyncio.sleep(config.PROCESSOR_ERROR_BACKOFF_SECONDS)
                else:
                    await self.maybe_flush_snapshots()

                if should_commit:
                    try:
                        await consumer.commit(record)
                    except KafkaConsumerError:
                        logger.exception(
                            "Kafka offset commit failed after feature processing",
                            extra=event_context.to_log_fields(),
                        )
                        await asyncio.sleep(config.PROCESSOR_ERROR_BACKOFF_SECONDS)
        finally:
            await self.flush_snapshots(force=True)
            self.runtime_state.consumer_running = False
            CONSUMER_RUNNING.set(0)

    async def stop(self) -> None:
        """Signal the consumer loop to stop and flush pending snapshots."""

        self._shutdown.set()
        await self.flush_snapshots(force=True)

    async def process_record(
        self,
        record: KafkaRecord,
        event_context: EventProcessingContext | None = None,
    ) -> None:
        """Validate and process a single Kafka record."""

        context = event_context or EventProcessingContext.from_record(record)
        try:
            event = InteractionEventV1Schema.model_validate(record.value)
        except ValidationError as exc:
            raise InvalidInteractionEventError(str(exc)) from exc

        updated_at = utc_now()
        content_feature = await self.feature_store.update_content_feature(
            event,
            updated_at=updated_at,
        )
        await self.feature_store.write_content_feature(content_feature)
        REDIS_MATERIALIZATIONS_TOTAL.inc()
        self._dirty_content_features[content_feature.content_id] = content_feature

        user_topic_feature: UserTopicAffinityRecord | None = None
        if event.topic:
            user_topic_feature = await self.feature_store.update_user_topic_affinity(
                event,
                updated_at=updated_at,
            )
            if user_topic_feature is not None:
                await self.feature_store.write_user_topic_affinity(user_topic_feature)
                REDIS_MATERIALIZATIONS_TOTAL.inc()
                self._dirty_user_topic_features[
                    (user_topic_feature.user_id, user_topic_feature.topic)
                ] = user_topic_feature

        self.runtime_state.processed_events_total += 1
        self.runtime_state.last_processed_at = updated_at
        self.runtime_state.dirty_content_feature_count = len(self._dirty_content_features)
        self.runtime_state.dirty_user_topic_feature_count = len(
            self._dirty_user_topic_features
        )
        EVENTS_PROCESSED_TOTAL.inc()
        LAST_PROCESSED_EVENT_UNIX.set(updated_at.timestamp())

        logger.info(
            "Interaction event materialized into ranking features",
            extra={
                **context.to_log_fields(),
                "event_id": str(event.event_id),
                "event_type": event.event_type,
                "schema_name": event.schema_name,
                "content_id": str(event.content_id),
                "user_id": str(event.user_id),
                "content_trending_score": content_feature.trending_score,
                "topic_affinity_score": (
                    user_topic_feature.affinity_score
                    if user_topic_feature is not None
                    else None
                ),
            },
        )

    async def maybe_flush_snapshots(self) -> None:
        """Flush dirty snapshots when the configured threshold is reached."""

        current_time = utc_now()
        dirty_count = (
            len(self._dirty_content_features) + len(self._dirty_user_topic_features)
        )
        if dirty_count == 0:
            return

        seconds_since_last_flush = (
            current_time - self._last_snapshot_flush_attempt
        ).total_seconds()
        if (
            dirty_count < self.snapshot_batch_size
            and seconds_since_last_flush < self.snapshot_flush_interval_seconds
        ):
            return

        await self.flush_snapshots()

    async def flush_snapshots(self, force: bool = False) -> None:
        """Persist dirty feature snapshots to PostgreSQL."""

        if (
            not force
            and not self._dirty_content_features
            and not self._dirty_user_topic_features
        ):
            return

        async with self._flush_lock:
            if (
                not self._dirty_content_features
                and not self._dirty_user_topic_features
            ):
                return

            snapshot_at = utc_now()
            content_features = list(self._dirty_content_features.values())
            user_topic_features = list(self._dirty_user_topic_features.values())

            await self.snapshot_repository.write_snapshots(
                content_features=content_features,
                user_topic_features=user_topic_features,
                snapshot_at=snapshot_at,
            )

            self._dirty_content_features.clear()
            self._dirty_user_topic_features.clear()
            self._last_snapshot_flush_attempt = snapshot_at
            self.runtime_state.last_snapshot_at = snapshot_at
            self.runtime_state.dirty_content_feature_count = 0
            self.runtime_state.dirty_user_topic_feature_count = 0
            self.runtime_state.database_available = True
            SNAPSHOT_FLUSH_TOTAL.inc()
            LAST_SNAPSHOT_FLUSH_UNIX.set(snapshot_at.timestamp())

            logger.info(
                "Feature snapshots flushed",
                extra={
                    "snapshot_at": snapshot_at.isoformat(),
                    "content_feature_count": len(content_features),
                    "user_topic_feature_count": len(user_topic_features),
                },
            )

    async def _check_database(self) -> bool:
        """Return whether PostgreSQL is currently reachable."""

        try:
            return await self.snapshot_repository.ping()
        except Exception:
            return False

    async def _check_redis(self) -> bool:
        """Return whether Redis is currently reachable."""

        try:
            return await self.feature_store.ping()
        except Exception:
            return False


__all__ = [
    "EventProcessingContext",
    "FeatureProcessorRuntimeState",
    "FeatureProcessorService",
    "FeatureSnapshotRepository",
    "InvalidInteractionEventError",
]
