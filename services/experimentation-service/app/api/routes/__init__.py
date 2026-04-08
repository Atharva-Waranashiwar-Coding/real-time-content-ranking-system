"""API routes for experimentation-service."""

from app.api.routes.experiments import router as experiments_router
from app.api.routes.health import router as health_router

__all__ = [
    "experiments_router",
    "health_router",
]
