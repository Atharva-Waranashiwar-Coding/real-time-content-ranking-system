"""API routes for interaction-service."""

from app.api.routes.health import router as health_router
from app.api.routes.interactions import (
    get_event_producer,
)
from app.api.routes.interactions import (
    router as interactions_router,
)

__all__ = ["get_event_producer", "health_router", "interactions_router"]
