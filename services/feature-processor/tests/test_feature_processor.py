"""Tests for feature-processor runtime and materialization behavior."""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest
from app.models import ContentFeatureSnapshot, UserTopicFeatureSnapshot
from app.services import InvalidInteractionEventError
from sqlalchemy import select

from shared_clients import KafkaRecord
from shared_schemas import INTERACTION_EVENT_V1_SCHEMA_NAME, InteractionEventV1Schema, utc_now


async def _fetch_snapshot_counts(session_factory) -> tuple[int, int]:
    """Return the number of stored content and user-topic snapshots."""

    async with session_factory() as session:
        content_result = await session.execute(select(ContentFeatureSnapshot))
        user_result = await session.execute(select(UserTopicFeatureSnapshot))
        return (
            len(content_result.scalars().all()),
            len(user_result.scalars().all()),
        )


def _build_record(**overrides) -> KafkaRecord:
    """Create a Kafka record using the shared interaction schema."""

    event = InteractionEventV1Schema(
        event_id=uuid4(),
        event_type="like",
        user_id=uuid4(),
        content_id=uuid4(),
        topic="backend",
        event_timestamp=utc_now(),
        metadata={"surface": "home_feed"},
        **overrides,
    )
    return KafkaRecord(
        topic="interactions.events.v1",
        key=str(event.user_id),
        value=event.model_dump(mode="json"),
        headers={
            "schema-name": INTERACTION_EVENT_V1_SCHEMA_NAME,
            "request-id": "req-123",
            "correlation-id": "corr-123",
        },
        partition=0,
        offset=1,
    )


class TestFeatureProcessor:
    """Feature processor runtime tests."""

    def test_process_record_materializes_content_and_user_features(
        self,
        processor_service,
        fake_redis,
        session_factory,
    ):
        """Valid interaction events should materialize Redis features and snapshots."""

        record = _build_record()

        asyncio.run(processor_service.process_record(record))
        asyncio.run(processor_service.flush_snapshots(force=True))

        payload = record.value
        content_key = processor_service.feature_store.content_feature_key(payload["content_id"])
        user_key = processor_service.feature_store.user_topic_affinity_key(payload["user_id"])

        content_hash = asyncio.run(fake_redis.hgetall(content_key))
        user_hash = asyncio.run(fake_redis.hgetall(user_key))
        content_snapshot_count, user_snapshot_count = asyncio.run(
            _fetch_snapshot_counts(session_factory)
        )

        assert content_hash["schema_name"] == "content_features.v1"
        assert content_hash["likes"] == "1"
        assert content_hash["topic"] == "backend"
        assert user_hash["schema_name"] == "user_topic_affinity.v1"
        assert float(user_hash["topic_affinity.backend"]) > 0
        assert processor_service.runtime_state.processed_events_total == 1
        assert content_snapshot_count == 1
        assert user_snapshot_count == 1

    def test_process_record_is_idempotent_for_duplicate_event_ids(
        self,
        processor_service,
        fake_redis,
    ):
        """Reprocessing the same Kafka record should not double count rolling metrics."""

        record = _build_record()

        asyncio.run(processor_service.process_record(record))
        asyncio.run(processor_service.process_record(record))

        payload = record.value
        content_key = processor_service.feature_store.content_feature_key(payload["content_id"])
        user_key = processor_service.feature_store.user_topic_affinity_key(payload["user_id"])

        content_hash = asyncio.run(fake_redis.hgetall(content_key))
        user_hash = asyncio.run(fake_redis.hgetall(user_key))

        assert content_hash["likes"] == "1"
        assert float(user_hash["topic_affinity.backend"]) > 0

    def test_process_record_rejects_invalid_payload(
        self,
        processor_service,
        fake_redis,
    ):
        """Invalid Kafka payloads should raise a non-retryable validation error."""

        invalid_record = KafkaRecord(
            topic="interactions.events.v1",
            key="user-1",
            value={"event_id": str(uuid4()), "event_type": "click"},
            headers={},
            partition=0,
            offset=2,
        )

        with pytest.raises(InvalidInteractionEventError):
            asyncio.run(processor_service.process_record(invalid_record))

        assert fake_redis.hashes == {}

    def test_health_and_metrics_endpoints(self, client):
        """Health and metrics routes should expose processor runtime state."""

        health_response = client.get("/api/v1/health")
        metrics_response = client.get("/metrics")

        assert health_response.status_code == 200
        assert health_response.json()["service"] == "feature-processor"
        assert metrics_response.status_code == 200
        assert "feature_processor_events_processed_total" in metrics_response.text
