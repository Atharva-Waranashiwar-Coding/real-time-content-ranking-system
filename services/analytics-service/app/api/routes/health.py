"""Health check endpoints for analytics-service."""

from datetime import datetime
from fastapi import APIRouter
from shared_schemas import HealthCheckResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Check service health."""
    return HealthCheckResponse(
        status="healthy",
        service="analytics-service",
        timestamp=datetime.utcnow(),
    )


@router.get("/ready", response_model=HealthCheckResponse)
async def readiness_check():
    """Check service readiness."""
    return HealthCheckResponse(
        status="ready",
        service="analytics-service",
        timestamp=datetime.utcnow(),
    )
