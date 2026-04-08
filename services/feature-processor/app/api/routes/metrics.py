"""Prometheus metrics endpoint for feature-processor."""

from fastapi import APIRouter, Response

from shared_logging import render_prometheus_metrics
from shared_logging.metrics import CONTENT_TYPE_LATEST

router = APIRouter(include_in_schema=False)


@router.get("/metrics")
async def metrics() -> Response:
    """Expose Prometheus metrics for scraping."""

    return Response(
        content=render_prometheus_metrics(),
        media_type=CONTENT_TYPE_LATEST,
    )
