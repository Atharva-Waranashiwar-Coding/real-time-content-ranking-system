"""Prometheus metrics for feature-processor."""

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest

EVENTS_PROCESSED_TOTAL = Counter(
    "feature_processor_events_processed_total",
    "Total number of interaction events processed successfully",
)
EVENTS_FAILED_TOTAL = Counter(
    "feature_processor_events_failed_total",
    "Total number of interaction events that failed processing",
)
SNAPSHOT_FLUSH_TOTAL = Counter(
    "feature_processor_snapshot_flush_total",
    "Total number of periodic snapshot flush operations",
)
REDIS_MATERIALIZATIONS_TOTAL = Counter(
    "feature_processor_redis_materializations_total",
    "Total number of Redis materialization writes",
)
CONSUMER_RUNNING = Gauge(
    "feature_processor_consumer_running",
    "Whether the Kafka consumer loop is currently running",
)
LAST_PROCESSED_EVENT_UNIX = Gauge(
    "feature_processor_last_processed_event_unix",
    "Unix timestamp of the last successfully processed event",
)
LAST_SNAPSHOT_FLUSH_UNIX = Gauge(
    "feature_processor_last_snapshot_flush_unix",
    "Unix timestamp of the last successful snapshot flush",
)


def render_prometheus_metrics() -> bytes:
    """Render the current Prometheus metrics payload."""

    return generate_latest()


__all__ = [
    "CONSUMER_RUNNING",
    "CONTENT_TYPE_LATEST",
    "EVENTS_FAILED_TOTAL",
    "EVENTS_PROCESSED_TOTAL",
    "LAST_PROCESSED_EVENT_UNIX",
    "LAST_SNAPSHOT_FLUSH_UNIX",
    "REDIS_MATERIALIZATIONS_TOTAL",
    "SNAPSHOT_FLUSH_TOTAL",
    "render_prometheus_metrics",
]
