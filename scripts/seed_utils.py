"""Utility functions for seed scripts."""

import importlib.util
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_local_package(module_name: str, relative_directory: str) -> None:
    """Load a local package with a stable import alias."""

    if module_name in sys.modules:
        return

    package_root = PROJECT_ROOT / relative_directory
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

sys.path.insert(0, str(PROJECT_ROOT / "services" / "user-service"))
sys.path.insert(0, str(PROJECT_ROOT / "services" / "content-service"))

load_dotenv()


def get_database_url(service_name: str = "user") -> str:
    """Get database URL from environment or config."""
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    user = os.getenv("DB_USER", "rankinguser")
    password = os.getenv("DB_PASSWORD", "rankingpass")
    db_name = os.getenv("DB_NAME", "ranking_db")

    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db_name}"


async def get_async_session(database_url: str = None):
    """Create an async database session."""
    if database_url is None:
        database_url = get_database_url()

    engine = create_async_engine(database_url, echo=False, future=True)
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    return async_session, engine


def print_step(step: str, message: str):
    """Print a step message with formatting."""
    print(f"\n✓ [{step}] {message}")


def print_error(message: str):
    """Print an error message."""
    print(f"\n✗ ERROR: {message}", file=sys.stderr)


def print_success(message: str):
    """Print a success message."""
    print(f"\n✓ SUCCESS: {message}")
