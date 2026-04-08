"""Main application for content-service."""

from contextlib import asynccontextmanager

from app.api.routes import content_router, health_router
from app.core import build_request_context, config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared_logging import build_metrics_router, install_http_observability, setup_logging

logger = setup_logging(config.SERVICE_NAME, config.LOG_LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""

    logger.info(
        "Starting content-service",
        extra={"service_name": config.SERVICE_NAME, "service_port": config.SERVICE_PORT},
    )
    yield
    logger.info(
        "Shutting down content-service",
        extra={"service_name": config.SERVICE_NAME},
    )


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

install_http_observability(
    app,
    service_name=config.SERVICE_NAME,
    logger=logger,
    build_request_context=build_request_context,
    request_id_header=config.REQUEST_ID_HEADER,
    correlation_id_header=config.CORRELATION_ID_HEADER,
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(content_router)
app.include_router(build_metrics_router())


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
