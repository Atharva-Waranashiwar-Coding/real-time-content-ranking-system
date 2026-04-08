# Feature Processor

Base URL: `http://localhost:8008`

`feature-processor` is not a public content API. It is a real-time stream processor that consumes Kafka topic `interactions.events.v1`, materializes ranking features into Redis, and persists periodic snapshots into PostgreSQL.

## Input Topic

- Topic: `interactions.events.v1`
- Input schema: `interaction_event.v1`

The processor validates every consumed payload against the shared `interaction_event.v1` contract before updating any feature state.

## Feature Schemas

### Content Features

- Schema name: `content_features.v1`
- Redis key: `feature:content:{content_id}:v1`
- Rolling metric keys: `feature:content:{content_id}:metric:{metric_name}:rolling-window:v1`

Materialized content fields:

- `impressions`
- `clicks`
- `likes`
- `saves`
- `skip_count`
- `watch_starts`
- `watch_completes`
- `ctr`
- `like_rate`
- `save_rate`
- `skip_rate`
- `completion_rate`
- `trending_score`
- `last_event_at`
- `updated_at`

### User Topic Affinity

- Schema name: `user_topic_affinity.v1`
- Redis key: `feature:user:{user_id}:topic-affinity:v1`
- Rolling metric keys: `feature:user:{user_id}:topic:{topic}:metric:{metric_name}:rolling-window:v1`

Materialized user affinity fields:

- `topic_affinity.{topic}`
- `last_event_at`
- `updated_at`
- `window_hours`

Affinity scores are weighted from rolling interaction counts. Positive actions (`click`, `like`, `save`, `watch_complete`) increase affinity. Negative actions (`skip`) decrease affinity.

## Snapshot Storage

Periodic snapshots are written to PostgreSQL:

- `content_feature_snapshots`
- `user_topic_feature_snapshots`

Snapshot rows are append-only and represent the latest dirty materialized vectors at the flush boundary. This keeps Redis optimized for serving latency and PostgreSQL optimized for history, replay support, and offline inspection.

## Rolling Window

- Window size: `24` hours by default
- Window configuration env var: `FEATURE_WINDOW_HOURS`

Rolling counts are maintained with Redis sorted sets keyed by event timestamp. Old members outside the configured window are pruned during ingestion.

## Endpoints

### `GET /api/v1/health`

Returns liveness plus current processor state:

- consumer running status
- Redis availability
- PostgreSQL availability
- last processed event time
- last snapshot flush time
- dirty feature counts

### `GET /api/v1/ready`

Returns `200 OK` when:

- Redis is reachable
- PostgreSQL is reachable
- the Kafka consumer loop is running when consumer auto-start is enabled

Returns `503 Service Unavailable` when any readiness dependency is unavailable.

### `GET /metrics`

### `GET /api/v1/metrics`

Prometheus metrics exposed by the processor include:

- `feature_processor_events_processed_total`
- `feature_processor_events_failed_total`
- `feature_processor_snapshot_flush_total`
- `feature_processor_redis_materializations_total`
- `feature_processor_consumer_running`

## Error Strategy

Invalid consumed events:

- are rejected by shared-schema validation
- are logged with request/correlation IDs when available
- are treated as non-retryable and their offsets are committed

Transient processing failures:

- are logged with Kafka topic, partition, and offset context
- do not advance the consumer offset
- rely on Kafka redelivery after retry/restart

Snapshot flush failures:

- leave dirty in-memory feature batches intact
- do not clear pending snapshot state until persistence succeeds

This keeps the processor deterministic and avoids silently dropping feature updates under transient Redis or PostgreSQL failures.
