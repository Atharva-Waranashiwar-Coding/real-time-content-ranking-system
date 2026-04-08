"""Tests for interaction ingestion endpoints."""

import asyncio
from uuid import uuid4

from app.models import Interaction
from sqlalchemy import select

from shared_schemas import (
    INTERACTION_EVENT_V1_SCHEMA_NAME,
    INTERACTIONS_EVENTS_V1_TOPIC,
)


async def _get_interaction_by_event_id(session_factory, event_id: str) -> Interaction | None:
    """Fetch a stored interaction by event ID."""

    async with session_factory() as session:
        result = await session.execute(
            select(Interaction).where(Interaction.event_id == event_id)
        )
        return result.scalars().first()


class TestInteractionEndpoints:
    """Test cases for interaction ingestion."""

    def test_ingest_interaction_success(self, client):
        """Test valid interaction ingestion persists and publishes."""

        payload = {
            "event_id": str(uuid4()),
            "event_type": "click",
            "user_id": str(uuid4()),
            "content_id": str(uuid4()),
            "session_id": "session-123",
            "topic": "Backend",
            "metadata": {"surface": "home_feed"},
        }

        response = client.post(
            "/api/v1/interactions",
            json=payload,
            headers={"X-Request-ID": "req-123", "X-Correlation-ID": "corr-123"},
        )

        assert response.status_code == 202
        data = response.json()
        assert data["event_id"] == payload["event_id"]
        assert data["schema_name"] == INTERACTION_EVENT_V1_SCHEMA_NAME
        assert data["kafka_topic"] == INTERACTIONS_EVENTS_V1_TOPIC
        assert data["request_id"] == "req-123"
        assert data["correlation_id"] == "corr-123"
        assert data["published_at"] is not None

        assert len(client.kafka_producer.messages) == 1
        message = client.kafka_producer.messages[0]
        assert message.topic == INTERACTIONS_EVENTS_V1_TOPIC
        assert message.key == payload["user_id"]
        assert message.value["event_id"] == payload["event_id"]
        assert message.value["topic"] == "backend"

        stored_interaction = asyncio.run(
            _get_interaction_by_event_id(client.session_factory, payload["event_id"])
        )
        assert stored_interaction is not None
        assert stored_interaction.event_type == "click"
        assert stored_interaction.topic == "backend"
        assert stored_interaction.request_id == "req-123"
        assert stored_interaction.correlation_id == "corr-123"
        assert stored_interaction.published_at is not None

    def test_ingest_interaction_invalid_payload(self, client):
        """Test payload validation errors."""

        payload = {
            "event_id": str(uuid4()),
            "event_type": "watch_complete",
            "user_id": str(uuid4()),
            "content_id": str(uuid4()),
            "watch_duration_seconds": 0,
        }

        response = client.post("/api/v1/interactions", json=payload)

        assert response.status_code == 422
        assert client.kafka_producer.messages == []

    def test_ingest_interaction_duplicate_event_id(self, client):
        """Test duplicate event IDs return a conflict."""

        payload = {
            "event_id": str(uuid4()),
            "event_type": "impression",
            "user_id": str(uuid4()),
            "content_id": str(uuid4()),
        }

        first_response = client.post("/api/v1/interactions", json=payload)
        second_response = client.post("/api/v1/interactions", json=payload)

        assert first_response.status_code == 202
        assert second_response.status_code == 409
        assert second_response.json()["detail"] == (
            f"Interaction event '{payload['event_id']}' already exists"
        )

    def test_ingest_interaction_kafka_publish_failure(self, client):
        """Test Kafka failure returns 503 but keeps the audit row."""

        client.kafka_producer.should_fail = True

        payload = {
            "event_id": str(uuid4()),
            "event_type": "save",
            "user_id": str(uuid4()),
            "content_id": str(uuid4()),
            "metadata": {"surface": "detail_page"},
        }

        response = client.post("/api/v1/interactions", json=payload)

        assert response.status_code == 503
        assert response.json()["detail"] == (
            "Interaction persisted but Kafka publish failed; retry is required"
        )

        stored_interaction = asyncio.run(
            _get_interaction_by_event_id(client.session_factory, payload["event_id"])
        )
        assert stored_interaction is not None
        assert stored_interaction.published_at is None

    def test_root_endpoint(self, client):
        """Test root endpoint."""

        response = client.get("/")

        assert response.status_code == 200
        assert response.json()["service"] == "interaction-service"
