"""Shared helpers for health, readiness, and liveness endpoints."""

from __future__ import annotations

from collections.abc import Callable

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from shared_schemas import HealthCheckResponse, utc_now


def build_health_response(*, service_name: str, status: str) -> HealthCheckResponse:
    """Build a standard health response with a UTC timestamp."""

    return HealthCheckResponse(
        status=status,
        service=service_name,
        timestamp=utc_now(),
    )


async def check_database_session_factory(
    session_factory: Callable[[], AsyncSession],
) -> bool:
    """Return whether a SQLAlchemy async session factory can answer `SELECT 1`."""

    try:
        async with session_factory() as session:
            result = await session.execute(text("SELECT 1"))
            return result.scalar_one() == 1
    except Exception:
        return False


async def check_redis_client(redis_client: object | None) -> bool:
    """Return whether the provided Redis client responds to `PING`."""

    if redis_client is None:
        return False

    try:
        return bool(await redis_client.ping())
    except Exception:
        return False


__all__ = [
    "build_health_response",
    "check_database_session_factory",
    "check_redis_client",
]
