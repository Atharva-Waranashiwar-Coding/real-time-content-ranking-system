"""Main application for interaction-service."""

from contextlib import asynccontextmanager

from app.api.routes import health_router, interactions_router
from app.core import build_request_context, config
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from shared_clients import create_kafka_producer
from shared_logging import setup_logging

logger = setup_logging(config.SERVICE_NAME, config.LOG_LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""

    logger.info(
        "Starting interaction-service",
        extra={"service_name": config.SERVICE_NAME, "service_port": config.SERVICE_PORT},
    )

    created_kafka_producer = False
    if not hasattr(app.state, "kafka_producer"):
        app.state.kafka_producer = create_kafka_producer(
            bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
            client_id=config.SERVICE_NAME,
        )
        created_kafka_producer = True

    try:
        yield
    finally:
        if created_kafka_producer and getattr(app.state, "kafka_producer", None) is not None:
            await app.state.kafka_producer.close()
            del app.state.kafka_producer

        logger.info(
            "Shutting down interaction-service",
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
app.include_router(interactions_router)


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
