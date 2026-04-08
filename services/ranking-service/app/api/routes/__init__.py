"""API routes for ranking-service."""

from app.api.routes.health import router as health_router
from app.api.routes.rankings import (
    get_event_producer,
)
from app.api.routes.rankings import (
    router as rankings_router,
)

__all__ = ["get_event_producer", "health_router", "rankings_router"]
