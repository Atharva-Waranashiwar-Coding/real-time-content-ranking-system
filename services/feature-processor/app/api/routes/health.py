"""Health check endpoints for feature-processor."""

from __future__ import annotations

from app.schemas import ProcessorHealthResponse
from app.services import FeatureProcessorRuntimeState, FeatureProcessorService
from fastapi import APIRouter, Request, Response, status

router = APIRouter(tags=["health"])


def get_feature_processor(request: Request) -> FeatureProcessorService | None:
    """Return the current feature processor runtime from application state."""

    return getattr(request.app.state, "feature_processor", None)


def get_runtime_state(request: Request) -> FeatureProcessorRuntimeState:
    """Return runtime state even when the processor has not been initialized yet."""

    return getattr(
        request.app.state,
        "feature_processor_runtime_state",
        FeatureProcessorRuntimeState(service_name="feature-processor"),
    )


@router.get("/health", response_model=ProcessorHealthResponse)
async def health_check(request: Request):
    """Return liveness and current runtime state."""

    feature_processor = get_feature_processor(request)
    if feature_processor is not None:
        await feature_processor.refresh_dependency_status()
        return feature_processor.runtime_state.to_response(status="healthy")

    return get_runtime_state(request).to_response(status="starting")


@router.get("/ready", response_model=ProcessorHealthResponse)
async def readiness_check(request: Request, response: Response):
    """Return readiness based on dependency status and consumer availability."""

    feature_processor = get_feature_processor(request)
    if feature_processor is not None:
        runtime_state = await feature_processor.refresh_dependency_status()
    else:
        runtime_state = get_runtime_state(request)

    is_ready = (
        runtime_state.redis_available
        and runtime_state.database_available
        and (
            runtime_state.consumer_running
            or not getattr(request.app.state, "feature_processor_should_start_consumer", True)
        )
    )

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return runtime_state.to_response(status="ready" if is_ready else "degraded")
