"""Test fixtures for feature-processor."""

from __future__ import annotations

import asyncio
import importlib.util
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "feature-processor"

os.environ["DEBUG"] = "false"
os.environ.setdefault("LOG_LEVEL", "INFO")
os.environ["FEATURE_PROCESSOR_START_CONSUMER"] = "false"


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

from app.db.base import Base  # noqa: E402
from app.main import app  # noqa: E402
from app.models import ContentFeatureSnapshot, UserTopicFeatureSnapshot  # noqa: E402
from app.services import (  # noqa: E402
    FeatureProcessorRuntimeState,
    FeatureProcessorService,
    FeatureSnapshotRepository,
    RedisFeatureStore,
)


class InMemoryRedis:
    """Async Redis test double that supports the feature store API."""

    def __init__(self):
        self.hashes: dict[str, dict[str, str]] = {}
        self.sorted_sets: dict[str, dict[str, float]] = {}

    async def aclose(self) -> None:
        """Close the fake Redis client."""

        return None

    async def expire(self, name: str, time: int) -> bool:
        """Ignore TTL operations for tests."""

        return True

    async def hget(self, name: str, key: str) -> str | None:
        """Read a single hash field."""

        return self.hashes.get(name, {}).get(key)

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

    async def zadd(self, name: str, mapping: dict[str, float]) -> int:
        """Add or update sorted-set members."""

        bucket = self.sorted_sets.setdefault(name, {})
        for member, score in mapping.items():
            bucket[member] = float(score)
        return len(mapping)

    async def zcard(self, name: str) -> int:
        """Return the number of members in a sorted set."""

        return len(self.sorted_sets.get(name, {}))

    async def zremrangebyscore(self, name: str, min: float, max: float) -> int:
        """Remove sorted-set members whose scores fall within the range."""

        bucket = self.sorted_sets.get(name, {})
        removable_members = [
            member
            for member, score in bucket.items()
            if float(min) <= score <= float(max)
        ]
        for member in removable_members:
            del bucket[member]
        return len(removable_members)


@pytest.fixture
def fake_redis() -> InMemoryRedis:
    """Return an in-memory Redis test double."""

    return InMemoryRedis()


@pytest.fixture
def session_factory(tmp_path: Path):
    """Return an async SQLAlchemy session factory backed by SQLite."""

    database_url = f"sqlite+aiosqlite:///{tmp_path / 'feature-processor-test.db'}"
    engine = create_async_engine(database_url, future=True)
    testing_session_factory = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async def _prepare_database() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    async def _dispose_engine() -> None:
        await engine.dispose()

    asyncio.run(_prepare_database())
    yield testing_session_factory
    asyncio.run(_dispose_engine())


@pytest.fixture
def processor_service(fake_redis: InMemoryRedis, session_factory) -> FeatureProcessorService:
    """Return a feature processor service wired to fake Redis and SQLite."""

    return FeatureProcessorService(
        feature_store=RedisFeatureStore(fake_redis, window_hours=24),
        snapshot_repository=FeatureSnapshotRepository(session_factory),
        runtime_state=FeatureProcessorRuntimeState(service_name="feature-processor"),
        snapshot_batch_size=2,
        snapshot_flush_interval_seconds=1,
    )


@pytest.fixture
def client(
    fake_redis: InMemoryRedis,
    session_factory,
    processor_service: FeatureProcessorService,
) -> TestClient:
    """Create a TestClient using the fake Redis store and SQLite snapshots."""

    app.state.redis_client = fake_redis
    app.state.feature_processor_runtime_state = processor_service.runtime_state
    app.state.feature_processor = processor_service
    app.state.feature_processor_should_start_consumer = False

    with TestClient(app) as test_client:
        test_client.processor_service = processor_service
        test_client.fake_redis = fake_redis
        test_client.session_factory = session_factory
        yield test_client

    for attribute_name in (
        "feature_processor",
        "feature_processor_runtime_state",
        "feature_processor_should_start_consumer",
        "redis_client",
    ):
        if hasattr(app.state, attribute_name):
            delattr(app.state, attribute_name)


__all__ = [
    "ContentFeatureSnapshot",
    "InMemoryRedis",
    "UserTopicFeatureSnapshot",
]
