"""Health check endpoints for api-gateway."""

from app.core import config
from fastapi import APIRouter

from shared_logging import build_health_response
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
async def readiness_check():
    """Check service readiness."""
    return build_health_response(service_name=config.SERVICE_NAME, status="ready")
