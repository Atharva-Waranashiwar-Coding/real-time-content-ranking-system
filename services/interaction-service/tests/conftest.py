"""Test fixtures for interaction-service."""

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
SERVICE_ROOT = ROOT / "services" / "interaction-service"

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

from app.db import get_db  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.main import app  # noqa: E402

from shared_clients import KafkaProducerError  # noqa: E402


class FakeKafkaProducer:
    """Test double for Kafka publishing."""

    def __init__(self):
        self.messages = []
        self.should_fail = False

    async def publish(self, message) -> None:
        if self.should_fail:
            raise KafkaProducerError("Simulated Kafka failure")
        self.messages.append(message)

    async def close(self) -> None:
        return None


@pytest.fixture
def producer() -> FakeKafkaProducer:
    """Return a fake Kafka producer."""

    return FakeKafkaProducer()


@pytest.fixture
def client(tmp_path: Path, producer: FakeKafkaProducer) -> TestClient:
    """Create a TestClient backed by SQLite and a fake Kafka producer."""

    database_url = f"sqlite+aiosqlite:///{tmp_path / 'interaction-service-test.db'}"
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

    async def override_get_db():
        async with testing_session_factory() as session:
            yield session

    asyncio.run(_prepare_database())
    app.dependency_overrides[get_db] = override_get_db
    app.state.kafka_producer = producer

    with TestClient(app) as test_client:
        test_client.kafka_producer = producer
        test_client.session_factory = testing_session_factory
        yield test_client

    app.dependency_overrides.clear()
    if hasattr(app.state, "kafka_producer"):
        del app.state.kafka_producer
    asyncio.run(_dispose_engine())
