#!/usr/bin/env python3
"""Generate service skeleton files."""

from pathlib import Path

services = [
    "api-gateway",
    "user-service",
    "content-service",
    "interaction-service",
    "feed-service",
    "ranking-service",
    "experimentation-service",
    "analytics-service",
    "feature-processor",
]

base_path = Path("/Users/atharvawaranashiwar/Documents/Projects/content_ranking_system/services")

for i, service in enumerate(services):
    service_path = base_path / service
    port = 8000 + i
    
    # Create config.py
    config_file = service_path / "app" / "core" / "config.py"
    config_file.write_text(f'''"""Configuration for {service}."""

from shared_config import settings as base_settings


class ServiceConfig:
    """Service-specific configuration."""
    
    SERVICE_NAME = "{service}"
    SERVICE_PORT = {port}
    
    DEBUG = base_settings.DEBUG
    LOG_LEVEL = base_settings.LOG_LEVEL
    DATABASE_URL = base_settings.database_url
    REDIS_URL = base_settings.redis_url
    KAFKA_BOOTSTRAP_SERVERS = base_settings.KAFKA_BOOTSTRAP_SERVERS


config = ServiceConfig()
''')
    
    # Create health.py route
    health_file = service_path / "app" / "api" / "routes" / "health.py"
    health_file.write_text(f'''"""Health check endpoints for {service}."""

from datetime import datetime
from fastapi import APIRouter
from shared_schemas import HealthCheckResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Check service health."""
    return HealthCheckResponse(
        status="healthy",
        service="{service}",
        timestamp=datetime.utcnow(),
    )


@router.get("/ready", response_model=HealthCheckResponse)
async def readiness_check():
    """Check service readiness."""
    return HealthCheckResponse(
        status="ready",
        service="{service}",
        timestamp=datetime.utcnow(),
    )
''')
    
    # Create main.py
    main_file = service_path / "app" / "main.py"
    main_file.write_text(f'''"""Main application for {service}."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared_logging import setup_logging
from app.core.config import config
from app.api.routes import health

logger = setup_logging(config.SERVICE_NAME, config.LOG_LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    logger.info(f"Starting {{config.SERVICE_NAME}} on port {{config.SERVICE_PORT}}")
    yield
    logger.info(f"Shutting down {{config.SERVICE_NAME}}")


app = FastAPI(
    title=config.SERVICE_NAME,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {{"service": config.SERVICE_NAME, "version": "0.1.0"}}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=config.SERVICE_PORT,
        reload=config.DEBUG,
        log_level=config.LOG_LEVEL.lower(),
    )
''')
    
    print(f"✓ Created files for {service} (port {port})")

print("\n✓ All service skeleton files created")
