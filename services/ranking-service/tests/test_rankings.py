"""Tests for ranking-service endpoints."""

from datetime import timedelta
from uuid import uuid4

from shared_schemas import (
    RANKING_DECISIONS_V1_TOPIC,
    RANKING_REQUEST_V1_SCHEMA_NAME,
    utc_now,
)


def _build_candidate_payload(
    *,
    topic: str = "backend",
    category: str = "backend",
    user_topic_affinity: float = 0.5,
    published_at=None,
    trending_score: float = 0.0,
) -> dict:
    """Create a ranking candidate payload."""

    content_id = str(uuid4())
    return {
        "content_id": content_id,
        "title": f"Content {content_id}",
        "description": "Candidate content item",
        "topic": topic,
        "category": category,
        "published_at": (published_at or utc_now()).isoformat(),
        "candidate_sources": ["recent"],
        "user_topic_affinity": user_topic_affinity,
        "content_features": {
            "content_id": content_id,
            "topic": topic,
            "trending_score": trending_score,
            "ctr": 0.2,
            "like_rate": 0.1,
            "save_rate": 0.05,
            "skip_rate": 0.0,
            "completion_rate": 0.15,
        },
    }


class TestRankingEndpoints:
    """Endpoint tests for ranking-service."""

    def test_rankings_success_returns_ordered_items_and_publishes_event(self, client):
        """Ranking endpoint should return ordered items and emit a decision event."""

        payload = {
            "schema_name": RANKING_REQUEST_V1_SCHEMA_NAME,
            "user_id": str(uuid4()),
            "candidates": [
                _build_candidate_payload(
                    topic="backend",
                    user_topic_affinity=0.9,
                    trending_score=15.0,
                ),
                _build_candidate_payload(
                    topic="ai",
                    category="ai",
                    user_topic_affinity=0.3,
                    published_at=utc_now() - timedelta(days=3),
                    trending_score=2.0,
                ),
            ],
            "apply_diversity_penalty": True,
            "metadata": {"surface": "home_feed"},
        }

        response = client.post(
            "/api/v1/rankings",
            json=payload,
            headers={"X-Request-ID": "req-123", "X-Correlation-ID": "corr-123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["strategy_name"] == "rules_based.v1"
        assert data["candidate_count"] == 2
        assert len(data["ranked_items"]) == 2
        assert data["ranked_items"][0]["score"] >= data["ranked_items"][1]["score"]
        assert data["ranked_items"][0]["score_breakdown"]["final_score"] == data["ranked_items"][0]["score"]

        assert len(client.kafka_producer.messages) == 1
        message = client.kafka_producer.messages[0]
        assert message.topic == RANKING_DECISIONS_V1_TOPIC
        assert message.key == payload["user_id"]
        assert message.headers["request-id"] == "req-123"
        assert message.value["request_id"] == "req-123"
        assert message.value["correlation_id"] == "corr-123"

    def test_rankings_kafka_publish_failure_returns_503(self, client):
        """Kafka failures should surface as a 503 response."""

        client.kafka_producer.should_fail = True
        payload = {
            "user_id": str(uuid4()),
            "candidates": [_build_candidate_payload()],
        }

        response = client.post("/api/v1/rankings", json=payload)

        assert response.status_code == 503
        assert response.json()["detail"] == (
            "Ranking completed but decision event publication failed"
        )

    def test_rankings_empty_candidates_returns_empty_result(self, client):
        """The service should handle an empty candidate list deterministically."""

        payload = {"user_id": str(uuid4()), "candidates": []}

        response = client.post("/api/v1/rankings", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["candidate_count"] == 0
        assert data["ranked_items"] == []
