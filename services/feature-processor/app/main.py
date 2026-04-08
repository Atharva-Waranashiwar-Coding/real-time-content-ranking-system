"""Main application for feature-processor."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from app.api.routes import health_router, metrics_router
from app.core.config import config
from app.db import async_session
from app.services import (
    FeatureProcessorRuntimeState,
    FeatureProcessorService,
    FeatureSnapshotRepository,
    RedisFeatureStore,
)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared_clients import create_kafka_consumer
from shared_logging import setup_logging

logger = setup_logging(config.SERVICE_NAME, config.LOG_LEVEL)


def _build_feature_processor(app: FastAPI) -> FeatureProcessorService:
    """Build the feature processor runtime from application state."""

    return FeatureProcessorService(
        feature_store=RedisFeatureStore(
            redis_client=app.state.redis_client,
            window_hours=config.FEATURE_WINDOW_HOURS,
        ),
        snapshot_repository=FeatureSnapshotRepository(async_session),
        runtime_state=app.state.feature_processor_runtime_state,
        snapshot_batch_size=config.FEATURE_SNAPSHOT_BATCH_SIZE,
        snapshot_flush_interval_seconds=config.FEATURE_SNAPSHOT_FLUSH_INTERVAL_SECONDS,
    )


def _ensure_redis_client(app: FastAPI) -> bool:
    """Create the shared Redis client if the app does not already have one."""

    if hasattr(app.state, "redis_client"):
        return False

    import redis.asyncio as redis

    app.state.redis_client = redis.from_url(
        config.REDIS_URL,
        decode_responses=True,
    )
    return True


def _ensure_kafka_consumer(app: FastAPI) -> bool:
    """Create the shared Kafka consumer if the app does not already have one."""

    if hasattr(app.state, "kafka_consumer"):
        return False

    app.state.kafka_consumer = create_kafka_consumer(
        bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
        client_id=config.SERVICE_NAME,
        group_id=config.KAFKA_CONSUMER_GROUP,
        topics=[config.KAFKA_INTERACTIONS_TOPIC],
        auto_offset_reset=config.KAFKA_AUTO_OFFSET_RESET,
    )
    return True


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""

    logger.info(
        "Starting feature-processor",
        extra={"service_name": config.SERVICE_NAME, "service_port": config.SERVICE_PORT},
    )

    app.state.feature_processor_runtime_state = getattr(
        app.state,
        "feature_processor_runtime_state",
        FeatureProcessorRuntimeState(service_name=config.SERVICE_NAME),
    )
    app.state.feature_processor_should_start_consumer = config.FEATURE_PROCESSOR_START_CONSUMER

    created_redis_client = _ensure_redis_client(app)

    if not hasattr(app.state, "feature_processor"):
        app.state.feature_processor = _build_feature_processor(app)

    created_kafka_consumer = (
        config.FEATURE_PROCESSOR_START_CONSUMER and _ensure_kafka_consumer(app)
    )

    consumer_task: asyncio.Task | None = None
    if config.FEATURE_PROCESSOR_START_CONSUMER:
        consumer_task = asyncio.create_task(
            app.state.feature_processor.run_forever(app.state.kafka_consumer)
        )
        app.state.feature_processor_task = consumer_task

    try:
        yield
    finally:
        if hasattr(app.state, "feature_processor"):
            await app.state.feature_processor.stop()

        if consumer_task is not None:
            consumer_task.cancel()
            try:
                await consumer_task
            except asyncio.CancelledError:
                pass
            if hasattr(app.state, "feature_processor_task"):
                del app.state.feature_processor_task

        if created_kafka_consumer and getattr(app.state, "kafka_consumer", None) is not None:
            await app.state.kafka_consumer.close()
            del app.state.kafka_consumer

        if created_redis_client and getattr(app.state, "redis_client", None) is not None:
            await app.state.redis_client.aclose()
            del app.state.redis_client

        logger.info(
            "Shutting down feature-processor",
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

app.include_router(health_router, prefix="/api/v1")
app.include_router(metrics_router)
app.include_router(metrics_router, prefix="/api/v1")


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
