# Interaction Service API

Base URL: `http://localhost:8003/api/v1`

## Endpoint

### `POST /interactions`

Persist a validated interaction event for audit and replay, then publish it to Kafka topic `interactions.events.v1`.

```json
{
  "schema_name": "interaction_event.v1",
  "event_id": "3fef7a46-1465-45f4-9bf5-a8220eb3ad0b",
  "event_type": "click",
  "user_id": "ef28e4d5-7ba7-44e8-93a2-d7cbb70175ec",
  "content_id": "03483ec6-f48e-4e1b-bc09-7f1f0d57cc92",
  "session_id": "web-session-001",
  "topic": "backend",
  "watch_duration_seconds": 0,
  "event_timestamp": "2026-04-07T21:00:00Z",
  "metadata": {
    "surface": "home_feed",
    "device_type": "web"
  }
}
```

Returns `202 Accepted`:

```json
{
  "event_id": "3fef7a46-1465-45f4-9bf5-a8220eb3ad0b",
  "schema_name": "interaction_event.v1",
  "kafka_topic": "interactions.events.v1",
  "status": "accepted",
  "request_id": "req-123",
  "correlation_id": "corr-123",
  "received_at": "2026-04-07T21:00:00Z",
  "published_at": "2026-04-07T21:00:00Z"
}
```

Response headers:
- `X-Request-ID`
- `X-Correlation-ID`

## Supported Event Types

- `impression`
- `click`
- `like`
- `save`
- `skip`
- `watch_start`
- `watch_complete`

## Validation Rules

- `schema_name` must be `interaction_event.v1`
- `event_id`, `user_id`, `content_id` must be UUIDs
- `watch_duration_seconds` must be non-negative
- `watch_complete` requires `watch_duration_seconds > 0`
- `topic` is normalized to lowercase when provided
- Unknown fields are rejected

## Topic Naming

Kafka topics follow the repository convention:

`{domain}.{entity}.{version}`

Current interaction topic:

- `interactions.events.v1`

This keeps the event stream explicit, domain-scoped, and versioned for downstream consumers.

## Event Versioning

The request and published event contract is identified by:

- Schema name: `interaction_event.v1`
- Topic: `interactions.events.v1`

Version evolution strategy:

- New additive changes should prefer a new schema version rather than mutating `interaction_event.v1` semantics silently.
- Consumers should branch on `schema_name`.
- A future incompatible version should publish a new schema identifier and, if needed, a new topic such as `interactions.events.v2`.

## Error Strategy

- `422 Unprocessable Entity`: payload validation failed before persistence
- `409 Conflict`: duplicate `event_id`
- `503 Service Unavailable`: event was persisted for audit, but Kafka publish failed

Kafka publish failure behavior:

- The interaction row remains stored in PostgreSQL
- `published_at` remains `NULL`
- The persisted row is the replay source for retry or backfill tooling

Duplicate event behavior:

- `event_id` is the uniqueness boundary
- Re-sending an already ingested `event_id` returns `409 Conflict`

## Persistence Model

Interaction events are stored in PostgreSQL `interactions` for:

- immutable audit history
- replay into Kafka
- debugging ingestion failures
- downstream backfills
