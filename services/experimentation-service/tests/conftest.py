"""Test fixtures for experimentation-service."""

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
SERVICE_ROOT = ROOT / "services" / "experimentation-service"

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
sys.path.insert(0, str(SERVICE_ROOT))

from app.db import get_db  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.main import app  # noqa: E402


async def _create_tables(engine) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def _drop_tables(engine) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


@pytest.fixture
def client(tmp_path) -> TestClient:
    """Create a TestClient backed by a temporary SQLite database."""

    database_path = tmp_path / "experimentation.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{database_path}", future=True)
    test_sessionmaker = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    asyncio.run(_create_tables(engine))

    async def override_get_db():
        async with test_sessionmaker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    asyncio.run(_drop_tables(engine))
    asyncio.run(engine.dispose())
