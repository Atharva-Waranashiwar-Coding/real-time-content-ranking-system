"""Health check endpoints for feed-service."""

from fastapi import APIRouter

from shared_schemas import HealthCheckResponse, utc_now

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Check service health."""
    return HealthCheckResponse(
        status="healthy",
        service="feed-service",
        timestamp=utc_now(),
    )


@router.get("/ready", response_model=HealthCheckResponse)
async def readiness_check():
    """Check service readiness."""
    return HealthCheckResponse(
        status="ready",
        service="feed-service",
        timestamp=utc_now(),
    )
