"""Main application for api-gateway."""

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
    logger.info(f"Starting {config.SERVICE_NAME} on port {config.SERVICE_PORT}")
    yield
    logger.info(f"Shutting down {config.SERVICE_NAME}")


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
    return {"service": config.SERVICE_NAME, "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=config.SERVICE_PORT,
        reload=config.DEBUG,
        log_level=config.LOG_LEVEL.lower(),
    )
