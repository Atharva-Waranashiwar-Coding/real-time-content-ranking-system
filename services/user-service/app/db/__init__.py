"""Database utilities for user-service."""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import config

# Async engine for database connections
engine = create_async_engine(
    config.DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
)

# Async session factory
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    """Dependency to get database session."""
    async with async_session() as session:
        yield session
