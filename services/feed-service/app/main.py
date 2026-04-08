"""Main application for feed-service."""

from contextlib import asynccontextmanager

from app.api.routes import feed_router, health_router
from app.core import build_request_context, config
from app.services import (
    CandidateService,
    ContentCatalogClient,
    ExperimentationApiClient,
    FeedRedisStore,
    FeedService,
    RankingApiClient,
    UserContextClient,
)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared_logging import build_metrics_router, install_http_observability, setup_logging

logger = setup_logging(config.SERVICE_NAME, config.LOG_LEVEL)


def _build_feed_service(app: FastAPI) -> FeedService:
    """Build the feed assembly service from application state."""

    feature_store = FeedRedisStore(app.state.redis_client)
    candidate_service = CandidateService(
        content_client=ContentCatalogClient(config.CONTENT_SERVICE_URL),
        user_client=UserContextClient(config.USER_SERVICE_URL),
        feature_store=feature_store,
    )
    return FeedService(
        candidate_service=candidate_service,
        ranking_client=RankingApiClient(config.RANKING_SERVICE_URL),
        experimentation_client=ExperimentationApiClient(
            config.EXPERIMENTATION_SERVICE_URL
        ),
        feature_store=feature_store,
        cache_ttl_seconds=config.FEED_CACHE_TTL_SECONDS,
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""

    logger.info(
        "Starting feed-service",
        extra={"service_name": config.SERVICE_NAME, "service_port": config.SERVICE_PORT},
    )

    created_redis_client = _ensure_redis_client(app)
    if not hasattr(app.state, "feed_service"):
        app.state.feed_service = _build_feed_service(app)

    try:
        yield
    finally:
        if created_redis_client and getattr(app.state, "redis_client", None) is not None:
            await app.state.redis_client.aclose()
            del app.state.redis_client

        logger.info(
            "Shutting down feed-service",
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
app.include_router(feed_router)
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
