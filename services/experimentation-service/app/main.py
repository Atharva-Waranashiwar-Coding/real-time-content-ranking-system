"""Main application for experimentation-service."""

from contextlib import asynccontextmanager

from app.api.routes import experiments_router, health_router
from app.core import build_request_context, config
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from shared_logging import setup_logging

logger = setup_logging(config.SERVICE_NAME, config.LOG_LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""

    logger.info(
        "Starting experimentation-service",
        extra={"service_name": config.SERVICE_NAME, "service_port": config.SERVICE_PORT},
    )
    yield
    logger.info(
        "Shutting down experimentation-service",
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


@app.middleware("http")
async def attach_request_context(request: Request, call_next):
    """Attach request-scoped identifiers to the request and response."""

    request_context = build_request_context(request)
    request.state.request_context = request_context

    response = await call_next(request)
    response.headers[config.REQUEST_ID_HEADER] = request_context.request_id
    response.headers[config.CORRELATION_ID_HEADER] = request_context.correlation_id

    logger.info(
        "HTTP request completed",
        extra={
            **request_context.to_log_fields(),
            "status_code": response.status_code,
        },
    )
    return response


app.include_router(health_router, prefix="/api/v1")
app.include_router(experiments_router)


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
