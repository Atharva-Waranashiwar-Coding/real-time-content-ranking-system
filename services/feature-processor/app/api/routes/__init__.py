"""API routes for feature-processor."""

from app.api.routes.health import get_feature_processor
from app.api.routes.health import router as health_router
from app.api.routes.metrics import router as metrics_router

__all__ = ["get_feature_processor", "health_router", "metrics_router"]
