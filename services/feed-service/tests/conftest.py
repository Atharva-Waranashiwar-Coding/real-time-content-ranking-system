"""Test fixtures for feed-service."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "feed-service"

os.environ["DEBUG"] = "false"
os.environ.setdefault("LOG_LEVEL", "INFO")


def _load_local_package(module_name: str, relative_directory: str) -> None:
    """Load a local package under a stable import alias for tests."""

    if module_name in sys.modules:
        return

    package_root = ROOT / relative_directory
    module_path = package_root / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        module_name,
        module_path,
        submodule_search_locations=[str(package_root)],
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load package '{module_name}' from {module_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)


_load_local_package("shared_schemas", "packages/shared-schemas")
_load_local_package("shared_config", "packages/shared-config")
_load_local_package("shared_logging", "packages/shared-logging")
_load_local_package("shared_clients", "packages/shared-clients")
sys.path.insert(0, str(SERVICE_ROOT))

from app.main import app  # noqa: E402
from app.services import (  # noqa: E402
    CandidateService,
    FeedRedisStore,
    FeedService,
)

from shared_schemas import (  # noqa: E402
    ExperimentAssignmentV1Schema,
    ExperimentExposureV1Schema,
    RankedContentItemV1Schema,
    RankingResponseV1Schema,
    RankingScoreBreakdownV1Schema,
    utc_now,
)


class InMemoryRedis:
    """Async Redis test double for feed-service."""

    def __init__(self):
        self.hashes: dict[str, dict[str, str]] = {}
        self.values: dict[str, str] = {}

    async def aclose(self) -> None:
        """Close the fake client."""

        return None

    async def expire(self, name: str, time: int) -> bool:
        """Ignore TTL operations for tests."""

        return True

    async def get(self, name: str) -> str | None:
        """Read a cached string value."""

        return self.values.get(name)

    async def hgetall(self, name: str) -> dict[str, str]:
        """Read an entire hash."""

        return dict(self.hashes.get(name, {}))

    async def hset(self, name: str, mapping: dict[str, object]) -> int:
        """Write one or more hash fields."""

        bucket = self.hashes.setdefault(name, {})
        for key, value in mapping.items():
            bucket[key] = "" if value is None else str(value)
        return len(mapping)

    async def ping(self) -> bool:
        """Return a successful ping."""

        return True

    async def set(self, name: str, value: str, ex: int | None = None) -> bool:
        """Write a cached string value."""

        self.values[name] = value
        return True


class FakeUserContextClient:
    """Fake user-service client."""

    def __init__(self, user_response):
        self.user_response = user_response
        self.calls = 0

    async def get_user(self, user_id: str):
        self.calls += 1
        return self.user_response


class FakeContentCatalogClient:
    """Fake content-service client."""

    def __init__(self, items):
        self.items = items
        self.calls = []

    async def list_published_content(self, *, limit: int, topic: str | None = None):
        self.calls.append({"limit": limit, "topic": topic})
        filtered_items = [
            item for item in self.items if topic is None or item.topic == topic
        ]
        return filtered_items[:limit]


class FakeRankingApiClient:
    """Fake ranking-service client."""

    def __init__(self):
        self.calls = 0
        self.last_request = None
        self.last_headers = None

    async def rank_candidates(self, ranking_request, *, headers: dict[str, str]):
        self.calls += 1
        self.last_request = ranking_request
        self.last_headers = headers

        sorted_candidates = sorted(
            ranking_request.candidates,
            key=lambda candidate: (
                candidate.user_topic_affinity,
                candidate.content_features.trending_score,
                candidate.published_at,
                str(candidate.content_id),
            ),
            reverse=True,
        )
        ranked_items = [
            RankedContentItemV1Schema(
                **candidate.model_dump(mode="python"),
                rank=index,
                score=round(candidate.user_topic_affinity + candidate.content_features.trending_score / 100, 6),
                score_breakdown=RankingScoreBreakdownV1Schema(
                    user_topic_affinity=candidate.user_topic_affinity,
                    user_topic_affinity_weighted=round(candidate.user_topic_affinity * 0.35, 6),
                    recency=0.5,
                    recency_weighted=0.1,
                    engagement=0.2,
                    engagement_weighted=0.05,
                    trending=min(candidate.content_features.trending_score / 25, 1.0),
                    trending_weighted=round(min(candidate.content_features.trending_score / 25, 1.0) * 0.2, 6),
                    diversity_penalty=0.0,
                    final_score=round(candidate.user_topic_affinity + candidate.content_features.trending_score / 100, 6),
                ),
            )
            for index, candidate in enumerate(sorted_candidates, start=1)
        ]
        return RankingResponseV1Schema(
            decision_id="1f57d1ba-c6fd-4682-a243-6c5cc72dc5ff",
            user_id=ranking_request.user_id,
            strategy_name=ranking_request.strategy_name,
            candidate_count=len(ranking_request.candidates),
            ranked_items=ranked_items,
            generated_at=utc_now(),
        )


class FakeExperimentationApiClient:
    """Fake experimentation-service client."""

    def __init__(self):
        self.assignment_calls = 0
        self.exposure_calls = 0
        self.last_headers = None
        self.last_exposure_request = None
        self.assignment = ExperimentAssignmentV1Schema(
            experiment_key="home_feed_ranking.v1",
            variant_key="control",
            strategy_name="rules_v1",
            user_id="5f1a550d-0191-43c2-b25d-a7c5e2daa001",
            assignment_bucket=1234,
            assigned_at=utc_now(),
        )

    async def get_assignment(self, user_id: str, *, headers: dict[str, str]):
        self.assignment_calls += 1
        self.last_headers = headers
        return self.assignment

    async def record_exposure(self, exposure_request, *, headers: dict[str, str]):
        self.exposure_calls += 1
        self.last_headers = headers
        self.last_exposure_request = exposure_request
        return ExperimentExposureV1Schema(
            exposure_id=str(uuid4()),
            experiment_key=exposure_request.experiment_key,
            variant_key=exposure_request.variant_key,
            strategy_name=exposure_request.strategy_name,
            user_id=exposure_request.user_id,
            recorded_at=utc_now(),
        )


@pytest.fixture
def fake_redis() -> InMemoryRedis:
    """Return an in-memory Redis client."""

    return InMemoryRedis()


@pytest.fixture
def client_components(fake_redis):
    """Return the feed-service dependency bundle used by tests."""

    from app.schemas import UpstreamContentItem, UpstreamUserProfile, UpstreamUserResponse

    user_response = UpstreamUserResponse(
        id="5f1a550d-0191-43c2-b25d-a7c5e2daa001",
        username="ranking_fan",
        email="ranking@example.com",
        created_at=utc_now(),
        updated_at=utc_now(),
        profile=UpstreamUserProfile(
            id="6f1a550d-0191-43c2-b25d-a7c5e2daa002",
            user_id="5f1a550d-0191-43c2-b25d-a7c5e2daa001",
            bio="Enjoys backend and AI systems",
            topic_preferences={"backend": 0.9, "ai": 0.6},
            created_at=utc_now(),
            updated_at=utc_now(),
        ),
    )
    content_items = [
        UpstreamContentItem(
            id="c1000000-0000-0000-0000-000000000001",
            title="Backend Scaling Patterns",
            description="Backend content",
            topic="backend",
            category="backend",
            status="published",
            view_count=10,
            engagement_metadata={},
            created_at=utc_now(),
            published_at=utc_now(),
            updated_at=utc_now(),
            tags=[],
        ),
        UpstreamContentItem(
            id="c1000000-0000-0000-0000-000000000002",
            title="Modern AI Workflows",
            description="AI content",
            topic="ai",
            category="ai",
            status="published",
            view_count=10,
            engagement_metadata={},
            created_at=utc_now(),
            published_at=utc_now(),
            updated_at=utc_now(),
            tags=[],
        ),
        UpstreamContentItem(
            id="c1000000-0000-0000-0000-000000000003",
            title="System Design Interview Loops",
            description="System design content",
            topic="system-design",
            category="system-design",
            status="published",
            view_count=10,
            engagement_metadata={},
            created_at=utc_now(),
            published_at=utc_now(),
            updated_at=utc_now(),
            tags=[],
        ),
    ]
    user_client = FakeUserContextClient(user_response)
    content_client = FakeContentCatalogClient(content_items)
    ranking_client = FakeRankingApiClient()
    experimentation_client = FakeExperimentationApiClient()

    feature_store = FeedRedisStore(fake_redis)
    candidate_service = CandidateService(
        content_client=content_client,
        user_client=user_client,
        feature_store=feature_store,
    )
    feed_service = FeedService(
        candidate_service=candidate_service,
        ranking_client=ranking_client,
        experimentation_client=experimentation_client,
        feature_store=feature_store,
        cache_ttl_seconds=60,
    )

    return {
        "content_client": content_client,
        "feature_store": feature_store,
        "feed_service": feed_service,
        "experimentation_client": experimentation_client,
        "ranking_client": ranking_client,
        "user_client": user_client,
        "user_response": user_response,
    }


@pytest.fixture
def client(fake_redis: InMemoryRedis, client_components) -> TestClient:
    """Create a TestClient backed by fake Redis and upstream clients."""

    app.state.redis_client = fake_redis
    app.state.feed_service = client_components["feed_service"]

    with TestClient(app) as test_client:
        test_client.fake_redis = fake_redis
        test_client.feed_service = client_components["feed_service"]
        test_client.experimentation_client = client_components["experimentation_client"]
        test_client.ranking_client = client_components["ranking_client"]
        test_client.content_client = client_components["content_client"]
        test_client.user_client = client_components["user_client"]
        test_client.user_response = client_components["user_response"]
        yield test_client

    for attribute_name in ("feed_service", "redis_client"):
        if hasattr(app.state, attribute_name):
            delattr(app.state, attribute_name)
