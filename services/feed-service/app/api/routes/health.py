"""Health check endpoints for feed-service."""

from app.core import config
from fastapi import APIRouter, Request, Response, status

from shared_logging import build_health_response, check_redis_client
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
async def readiness_check(request: Request, response: Response):
    """Check service readiness."""
    redis_available = await check_redis_client(getattr(request.app.state, "redis_client", None))
    if not redis_available:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return build_health_response(
        service_name=config.SERVICE_NAME,
        status="ready" if redis_available else "degraded",
    )
