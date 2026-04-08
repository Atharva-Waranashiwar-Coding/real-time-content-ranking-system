"""Tests for feed-service candidate retrieval and feed assembly."""

import asyncio

from shared_schemas import CandidateSource


class TestFeedEndpoint:
    """Endpoint tests for feed-service."""

    def test_get_feed_combines_recent_trending_and_topic_affinity_sources(
        self,
        client,
    ):
        """Feed generation should combine all configured candidate sources."""

        backend_affinity_key = (
            "feature:user:5f1a550d-0191-43c2-b25d-a7c5e2daa001:topic-affinity:v1"
        )
        asyncio.run(
            client.fake_redis.hset(
                backend_affinity_key,
                mapping={
                    "schema_name": "user_topic_affinity.v1",
                    "user_id": "5f1a550d-0191-43c2-b25d-a7c5e2daa001",
                    "topic_affinity.backend": "9.0",
                    "topic_affinity.ai": "4.0",
                },
            )
        )
        asyncio.run(
            client.fake_redis.hset(
                "feature:content:c1000000-0000-0000-0000-000000000001:v1",
                mapping={"trending_score": "20.0", "topic": "backend"},
            )
        )
        asyncio.run(
            client.fake_redis.hset(
                "feature:content:c1000000-0000-0000-0000-000000000002:v1",
                mapping={"trending_score": "30.0", "topic": "ai"},
            )
        )

        response = client.get(
            "/api/v1/feed?user_id=5f1a550d-0191-43c2-b25d-a7c5e2daa001&limit=10&offset=0"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["cache_hit"] is False
        assert data["total_candidates"] >= 3
        assert client.ranking_client.calls == 1

        candidate_sources = {
            str(candidate.content_id): set(candidate.candidate_sources)
            for candidate in client.ranking_client.last_request.candidates
        }
        assert CandidateSource.RECENT.value in candidate_sources[
            "c1000000-0000-0000-0000-000000000001"
        ]
        assert CandidateSource.TRENDING.value in candidate_sources[
            "c1000000-0000-0000-0000-000000000002"
        ]
        assert CandidateSource.TOPIC_AFFINITY.value in candidate_sources[
            "c1000000-0000-0000-0000-000000000001"
        ]

    def test_get_feed_uses_cache_on_repeat_requests(self, client):
        """Repeated requests for the same page should hit the Redis cache."""

        response_one = client.get(
            "/api/v1/feed?user_id=5f1a550d-0191-43c2-b25d-a7c5e2daa001&limit=2&offset=0"
        )
        response_two = client.get(
            "/api/v1/feed?user_id=5f1a550d-0191-43c2-b25d-a7c5e2daa001&limit=2&offset=0"
        )

        assert response_one.status_code == 200
        assert response_two.status_code == 200
        assert response_one.json()["cache_hit"] is False
        assert response_two.json()["cache_hit"] is True
        assert client.ranking_client.calls == 1

    def test_get_feed_paginates_ranked_results(self, client):
        """Feed pagination should slice the ranked result set correctly."""

        response = client.get(
            "/api/v1/feed?user_id=5f1a550d-0191-43c2-b25d-a7c5e2daa001&limit=1&offset=1"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 1
        assert data["offset"] == 1
        assert len(data["items"]) == 1
        assert data["has_more"] is True
        assert data["items"][0]["rank"] == 2

    def test_get_feed_returns_empty_result_when_no_candidates(self, client):
        """Empty candidate sets should not call ranking-service."""

        client.content_client.items = []

        response = client.get(
            "/api/v1/feed?user_id=5f1a550d-0191-43c2-b25d-a7c5e2daa001&limit=5&offset=0"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total_candidates"] == 0
