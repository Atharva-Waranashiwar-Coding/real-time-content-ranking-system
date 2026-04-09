# Observability

This document describes the shared telemetry surface, dead-letter strategy, and dashboard inventory for the platform.

## Telemetry Plan

- `api-gateway`: HTTP request count and latency, structured request logs, request/correlation ID propagation, `/metrics`, `/api/v1/live`, `/api/v1/ready`.
- `user-service`, `content-service`, `experimentation-service`, `analytics-service`: HTTP telemetry plus database-backed readiness checks.
- `feed-service`: HTTP telemetry, feed assembly latency, dependency request latency/retries for user/content/ranking/experimentation calls, and Redis-backed readiness.
- `interaction-service`: HTTP telemetry, Kafka publish throughput for `interactions.events.v1`, and readiness based on database plus producer availability.
- `ranking-service`: HTTP telemetry, ranking latency by strategy, Kafka publish throughput for `ranking.decisions.v1`, and producer-backed readiness.
- `feature-processor`: Kafka consume throughput, dead-letter throughput, consumer lag, dependency state for Redis/PostgreSQL, and `/api/v1/live` plus `/api/v1/ready`.

## Shared Metric Names

- `content_ranking_http_requests_total`
- `content_ranking_http_request_duration_seconds`
- `content_ranking_dependency_requests_total`
- `content_ranking_dependency_request_duration_seconds`
- `content_ranking_retry_attempts_total`
- `content_ranking_event_operations_total`
- `content_ranking_event_operation_duration_seconds`
- `content_ranking_ranking_duration_seconds`
- `content_ranking_feed_assembly_duration_seconds`
- `content_ranking_consumer_lag`

Feature-processor also keeps its existing service-specific counters such as `feature_processor_events_processed_total` and `feature_processor_events_failed_total`.

## Correlation and Tracing

The system uses pragmatic correlation-based tracing instead of a full distributed tracing backend:

- HTTP ingress creates or reuses `X-Request-ID` and `X-Correlation-ID`.
- Feed-service forwards those headers to upstream services.
- Interaction and ranking event publishers copy the identifiers into Kafka headers.
- Feature-processor copies the same identifiers into structured logs and dead-letter payloads.

This makes a single request observable across HTTP logs, Kafka events, and DLQ records without introducing a tracing collector.

## Dead-Letter Strategy

- Source topic: `interactions.events.v1`
- Dead-letter topic: `interactions.events.dlq.v1`
- Dead-letter schema: `dead_letter_event.v1`

Dead-letter publication rules:

- schema-invalid events go directly to the DLQ and are committed after successful DLQ publication
- processing errors are retried with bounded exponential backoff
- once retries are exhausted, the original record is published to the DLQ
- if DLQ publication fails, the record is not committed so the failure remains visible and retryable

The dead-letter payload includes the original topic, partition, offset, headers, request/correlation IDs, error type, error message, and the original event payload.

## Dashboard Inventory

Provisioned dashboards in Grafana:

1. `Platform Overview`
   - HTTP request rate by service
   - p95 HTTP latency by service
   - retry attempt volume by dependency
   - Prometheus scrape health
2. `Event Pipeline`
   - publish throughput for interaction and ranking topics
   - feature-processor consume throughput and failures
   - consumer lag by topic partition
   - dead-letter publications over the last 15 minutes
3. `Ranking and Feed Operations`
   - p95 ranking latency by strategy
   - p95 feed assembly latency split by cache hit
   - feed/ranking HTTP volume by route and status
   - dependency retry volume from feed-service

Grafana provisioning files live under [infra/docker/grafana/provisioning](../infra/docker/grafana/provisioning) and dashboard JSON files live under [infra/docker/grafana/dashboards](../infra/docker/grafana/dashboards).
