"""Health check endpoints for experimentation-service."""

from app.core import config
from app.db import async_session
from fastapi import APIRouter, Response, status

from shared_logging import build_health_response, check_database_session_factory
from shared_schemas import HealthCheckResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Check service health."""
    return build_health_response(service_name=config.SERVICE_NAME, status="healthy")


@router.get("/live", response_model=HealthCheckResponse)
async def liveness_check():
    """Check service liveness."""

    return build_health_response(service_name=config.SERVICE_NAME, status="alive")


@router.get("/ready", response_model=HealthCheckResponse)
async def readiness_check(response: Response):
    """Check service readiness."""
    database_available = await check_database_session_factory(async_session)
    if not database_available:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return build_health_response(
        service_name=config.SERVICE_NAME,
        status="ready" if database_available else "degraded",
    )
