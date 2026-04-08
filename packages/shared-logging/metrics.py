"""Shared Prometheus metrics and helpers."""

from __future__ import annotations

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

LATENCY_BUCKETS = (
    0.001,
    0.005,
    0.01,
    0.025,
    0.05,
    0.1,
    0.25,
    0.5,
    1.0,
    2.5,
    5.0,
)

HTTP_REQUESTS_TOTAL = Counter(
    "content_ranking_http_requests_total",
    "Total HTTP requests handled by service endpoints.",
    ["service", "method", "path", "status_code"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "content_ranking_http_request_duration_seconds",
    "HTTP request latency in seconds.",
    ["service", "method", "path"],
    buckets=LATENCY_BUCKETS,
)
DEPENDENCY_REQUESTS_TOTAL = Counter(
    "content_ranking_dependency_requests_total",
    "Total outbound dependency requests grouped by outcome.",
    ["service", "dependency", "operation", "outcome"],
)
DEPENDENCY_REQUEST_DURATION_SECONDS = Histogram(
    "content_ranking_dependency_request_duration_seconds",
    "Outbound dependency latency in seconds.",
    ["service", "dependency", "operation"],
    buckets=LATENCY_BUCKETS,
)
EVENT_OPERATIONS_TOTAL = Counter(
    "content_ranking_event_operations_total",
    "Kafka event publish/consume/DLQ operations.",
    ["service", "operation", "topic", "outcome"],
)
EVENT_OPERATION_DURATION_SECONDS = Histogram(
    "content_ranking_event_operation_duration_seconds",
    "Latency for Kafka event operations in seconds.",
    ["service", "operation", "topic"],
    buckets=LATENCY_BUCKETS,
)
RANKING_DURATION_SECONDS = Histogram(
    "content_ranking_ranking_duration_seconds",
    "Ranking computation latency by strategy.",
    ["service", "strategy"],
    buckets=LATENCY_BUCKETS,
)
FEED_ASSEMBLY_DURATION_SECONDS = Histogram(
    "content_ranking_feed_assembly_duration_seconds",
    "Feed assembly latency, including cache hits and ranking work.",
    ["service", "cache_hit"],
    buckets=LATENCY_BUCKETS,
)
RETRY_ATTEMPTS_TOTAL = Counter(
    "content_ranking_retry_attempts_total",
    "Total retry attempts against external dependencies.",
    ["service", "dependency", "operation"],
)
CONSUMER_LAG = Gauge(
    "content_ranking_consumer_lag",
    "Kafka consumer lag by partition.",
    ["service", "group_id", "topic", "partition"],
)


def observe_http_request(
    *,
    service_name: str,
    method: str,
    path: str,
    status_code: int,
    duration_seconds: float,
) -> None:
    """Record HTTP request count and latency."""

    labels = {
        "service": service_name,
        "method": method,
        "path": path,
    }
    HTTP_REQUESTS_TOTAL.labels(
        **labels,
        status_code=str(status_code),
    ).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(**labels).observe(duration_seconds)


def observe_dependency_request(
    *,
    service_name: str,
    dependency_name: str,
    operation: str,
    outcome: str,
    duration_seconds: float,
) -> None:
    """Record outbound dependency count and latency."""

    labels = {
        "service": service_name,
        "dependency": dependency_name,
        "operation": operation,
    }
    DEPENDENCY_REQUESTS_TOTAL.labels(
        **labels,
        outcome=outcome,
    ).inc()
    DEPENDENCY_REQUEST_DURATION_SECONDS.labels(**labels).observe(duration_seconds)


def record_retry_attempt(
    *,
    service_name: str,
    dependency_name: str,
    operation: str,
) -> None:
    """Record a retry attempt against an external dependency."""

    RETRY_ATTEMPTS_TOTAL.labels(
        service=service_name,
        dependency=dependency_name,
        operation=operation,
    ).inc()


def observe_event_operation(
    *,
    service_name: str,
    operation: str,
    topic: str,
    outcome: str,
    duration_seconds: float | None = None,
) -> None:
    """Record event operation throughput and optional latency."""

    labels = {
        "service": service_name,
        "operation": operation,
        "topic": topic,
    }
    EVENT_OPERATIONS_TOTAL.labels(
        **labels,
        outcome=outcome,
    ).inc()
    if duration_seconds is not None:
        EVENT_OPERATION_DURATION_SECONDS.labels(**labels).observe(duration_seconds)


def observe_ranking_duration(
    *,
    service_name: str,
    strategy_name: str,
    duration_seconds: float,
) -> None:
    """Record ranking computation latency."""

    RANKING_DURATION_SECONDS.labels(
        service=service_name,
        strategy=strategy_name,
    ).observe(duration_seconds)


def observe_feed_assembly_duration(
    *,
    service_name: str,
    cache_hit: bool,
    duration_seconds: float,
) -> None:
    """Record end-to-end feed assembly latency."""

    FEED_ASSEMBLY_DURATION_SECONDS.labels(
        service=service_name,
        cache_hit=str(cache_hit).lower(),
    ).observe(duration_seconds)


def observe_consumer_lag(
    *,
    service_name: str,
    group_id: str,
    topic: str,
    partition: int,
    lag: int,
) -> None:
    """Set the Kafka consumer lag gauge for a single partition."""

    CONSUMER_LAG.labels(
        service=service_name,
        group_id=group_id,
        topic=topic,
        partition=str(partition),
    ).set(lag)


def render_prometheus_metrics() -> bytes:
    """Render the current Prometheus registry."""

    return generate_latest()


def build_metrics_router() -> APIRouter:
    """Return a simple Prometheus `/metrics` router."""

    router = APIRouter(include_in_schema=False)

    @router.get("/metrics")
    async def metrics() -> Response:
        return Response(
            content=render_prometheus_metrics(),
            media_type=CONTENT_TYPE_LATEST,
        )

    return router


__all__ = [
    "CONTENT_TYPE_LATEST",
    "build_metrics_router",
    "observe_consumer_lag",
    "observe_dependency_request",
    "observe_event_operation",
    "observe_feed_assembly_duration",
    "observe_http_request",
    "observe_ranking_duration",
    "record_retry_attempt",
    "render_prometheus_metrics",
]
