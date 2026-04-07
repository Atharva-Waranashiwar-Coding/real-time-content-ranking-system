"""Utility functions for seed scripts."""

import os
import sys
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Add services to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "user-service"))
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "content-service"))

# Load environment variables
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
