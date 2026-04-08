"""Tests for analytics-service experiment comparison endpoints."""

import asyncio
from uuid import uuid4

from app.models import ExperimentExposure, ExperimentExposureItem, Interaction

from shared_schemas import utc_now


async def _seed_test_data(sessionmaker) -> None:
    """Seed experiment exposures and interactions for analytics tests."""

    user_a = str(uuid4())
    user_b = str(uuid4())
    content_a = str(uuid4())
    content_b = str(uuid4())
    content_c = str(uuid4())
    content_d = str(uuid4())
    now = utc_now()

    async with sessionmaker() as session:
        session.add_all(
            [
                ExperimentExposure(
                    id=str(uuid4()),
                    schema_name="experiment_exposure.v1",
                    experiment_key="home_feed_ranking.v1",
                    variant_key="control",
                    strategy_name="rules_v1",
                    user_id=user_a,
                    session_id="session-a",
                    request_id="req-a",
                    correlation_id="corr-a",
                    feed_limit=10,
                    feed_offset=0,
                    cache_hit=False,
                    generated_at=now,
                    created_at=now,
                    items=[
                        ExperimentExposureItem(
                            id=str(uuid4()),
                            content_id=content_a,
                            rank=1,
                            score=0.72,
                            topic="backend",
                            category="backend",
                            created_at=now,
                        ),
                        ExperimentExposureItem(
                            id=str(uuid4()),
                            content_id=content_b,
                            rank=2,
                            score=0.61,
                            topic="ai",
                            category="ai",
                            created_at=now,
                        ),
                    ],
                ),
                ExperimentExposure(
                    id=str(uuid4()),
                    schema_name="experiment_exposure.v1",
                    experiment_key="home_feed_ranking.v1",
                    variant_key="trending_boost",
                    strategy_name="rules_v2_with_trending_boost",
                    user_id=user_b,
                    session_id="session-b",
                    request_id="req-b",
                    correlation_id="corr-b",
                    feed_limit=10,
                    feed_offset=0,
                    cache_hit=False,
                    generated_at=now,
                    created_at=now,
                    items=[
                        ExperimentExposureItem(
                            id=str(uuid4()),
                            content_id=content_c,
                            rank=1,
                            score=0.79,
                            topic="backend",
                            category="backend",
                            created_at=now,
                        ),
                        ExperimentExposureItem(
                            id=str(uuid4()),
                            content_id=content_d,
                            rank=2,
                            score=0.66,
                            topic="devops",
                            category="devops",
                            created_at=now,
                        ),
                    ],
                ),
                Interaction(
                    id=str(uuid4()),
                    event_id=str(uuid4()),
                    schema_name="interaction_event.v1",
                    event_type="click",
                    user_id=user_a,
                    content_id=content_a,
                    session_id="session-a",
                    topic="backend",
                    watch_duration_seconds=0,
                    kafka_topic="interactions.events.v1",
                    request_id="req-click-a",
                    correlation_id="corr-click-a",
                    event_timestamp=now,
                    created_at=now,
                    published_at=now,
                ),
                Interaction(
                    id=str(uuid4()),
                    event_id=str(uuid4()),
                    schema_name="interaction_event.v1",
                    event_type="save",
                    user_id=user_a,
                    content_id=content_b,
                    session_id="session-a",
                    topic="ai",
                    watch_duration_seconds=0,
                    kafka_topic="interactions.events.v1",
                    request_id="req-save-a",
                    correlation_id="corr-save-a",
                    event_timestamp=now,
                    created_at=now,
                    published_at=now,
                ),
                Interaction(
                    id=str(uuid4()),
                    event_id=str(uuid4()),
                    schema_name="interaction_event.v1",
                    event_type="watch_complete",
                    user_id=user_b,
                    content_id=content_c,
                    session_id="session-b",
                    topic="backend",
                    watch_duration_seconds=42,
                    kafka_topic="interactions.events.v1",
                    request_id="req-complete-b",
                    correlation_id="corr-complete-b",
                    event_timestamp=now,
                    created_at=now,
                    published_at=now,
                ),
                Interaction(
                    id=str(uuid4()),
                    event_id=str(uuid4()),
                    schema_name="interaction_event.v1",
                    event_type="click",
                    user_id=user_b,
                    content_id=content_c,
                    session_id="session-b",
                    topic="backend",
                    watch_duration_seconds=0,
                    kafka_topic="interactions.events.v1",
                    request_id="req-click-b",
                    correlation_id="corr-click-b",
                    event_timestamp=now,
                    created_at=now,
                    published_at=now,
                ),
            ]
        )
        await session.commit()


class TestAnalyticsEndpoints:
    """Endpoint tests for analytics-service."""

    def test_experiment_comparison_aggregates_outcomes_by_strategy(self, client):
        """CTR, save rate, and completion rate should aggregate by strategy."""

        asyncio.run(_seed_test_data(client.test_sessionmaker))

        response = client.get("/api/v1/experiments/home_feed_ranking.v1/comparison")

        assert response.status_code == 200
        data = response.json()
        assert data["experiment_key"] == "home_feed_ranking.v1"
        assert len(data["strategies"]) == 2

        strategies = {item["strategy_name"]: item for item in data["strategies"]}
        assert strategies["rules_v1"]["item_exposures"] == 2
        assert strategies["rules_v1"]["clicks"] == 1
        assert strategies["rules_v1"]["saves"] == 1
        assert strategies["rules_v1"]["completions"] == 0
        assert strategies["rules_v1"]["ctr"] == 0.5
        assert strategies["rules_v1"]["save_rate"] == 0.5
        assert strategies["rules_v1"]["completion_rate"] == 0.0

        assert strategies["rules_v2_with_trending_boost"]["item_exposures"] == 2
        assert strategies["rules_v2_with_trending_boost"]["clicks"] == 1
        assert strategies["rules_v2_with_trending_boost"]["saves"] == 0
        assert strategies["rules_v2_with_trending_boost"]["completions"] == 1
        assert strategies["rules_v2_with_trending_boost"]["ctr"] == 0.5
        assert strategies["rules_v2_with_trending_boost"]["completion_rate"] == 0.5
