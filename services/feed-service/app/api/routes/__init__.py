"""API routes for feed-service."""

from app.api.routes.feed import get_feed_service
from app.api.routes.feed import router as feed_router
from app.api.routes.health import router as health_router

__all__ = ["feed_router", "get_feed_service", "health_router"]
