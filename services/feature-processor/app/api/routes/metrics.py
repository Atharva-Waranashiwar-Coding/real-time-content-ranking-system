"""Prometheus metrics endpoint for feature-processor."""

from app.core.metrics import CONTENT_TYPE_LATEST, render_prometheus_metrics
from fastapi import APIRouter, Response

router = APIRouter(include_in_schema=False)


@router.get("/metrics")
async def metrics() -> Response:
    """Expose Prometheus metrics for scraping."""

    return Response(
        content=render_prometheus_metrics(),
        media_type=CONTENT_TYPE_LATEST,
    )
