"""Health check endpoints for analytics-service."""

from fastapi import APIRouter

from shared_schemas import HealthCheckResponse, utc_now

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Check service health."""
    return HealthCheckResponse(
        status="healthy",
        service="analytics-service",
        timestamp=utc_now(),
    )


@router.get("/ready", response_model=HealthCheckResponse)
async def readiness_check():
    """Check service readiness."""
    return HealthCheckResponse(
        status="ready",
        service="analytics-service",
        timestamp=utc_now(),
    )
