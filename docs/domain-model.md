# Domain Model

## Core Persistent Entities

### `users`

- primary key: `id`
- unique fields: `username`, `email`
- purpose: durable user identity used by feed, interaction, experimentation, and analytics flows

### `user_profiles`

- one-to-one with `users` via `user_id`
- stores `bio` and `topic_preferences`
- purpose: explicit user preference baseline for ranking and demo explainability

### `content_items`

- primary key: `id`
- classification fields: `topic`, `category`, `status`
- operational fields: `published_at`, `view_count`, `engagement_metadata`
- purpose: catalog of draft and published learning content

### `content_tags` and `content_tags_association`

- many-to-many tag mapping for content taxonomy
- purpose: reusable content categorization and filter support

### `interactions`

- immutable interaction audit table
- idempotency field: `event_id`
- tracing fields: `request_id`, `correlation_id`
- replay fields: `event_payload`, `kafka_topic`, `published_at`
- purpose: durable audit trail for ingestion, replay, debugging, and analytics attribution

### `experiment_assignments`

- deterministic user-to-variant mapping by `experiment_key` and `user_id`
- stores `assignment_bucket`, `variant_key`, and `strategy_name`
- purpose: stable experiment assignment across repeated feed requests

### `experiment_exposures`

- one row per delivered feed response
- stores `experiment_key`, `variant_key`, `strategy_name`, `user_id`, `session_id`, pagination, and tracing fields
- purpose: the attribution boundary for experiment outcome analytics

### `experiment_exposure_items`

- child rows for each content item in an exposure
- stores `content_id`, `rank`, `score`, `topic`, and `category`
- purpose: attributed outcome denominator for CTR, save rate, and completion rate

### `content_feature_snapshots`

- append-only snapshots of materialized content metrics
- stores rolling counts plus derived rates such as `ctr`, `save_rate`, `completion_rate`, and `trending_score`
- purpose: durable history for low-latency content features

### `user_topic_feature_snapshots`

- append-only snapshots of per-user topic affinity entries
- stores rolling event counts plus `affinity_score`
- purpose: durable history for user-topic preference signals

## Low-Latency Serving Keys

### Content features

- key format: `feature:content:{content_id}:v1`
- fields:
  - `schema_name`
  - `topic`
  - `window_hours`
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

### User topic affinity

- key format: `feature:user:{user_id}:topic-affinity:v1`
- fields:
  - `schema_name`
  - `window_hours`
  - `last_event_at`
  - `updated_at`
  - `topic_affinity.{topic}`

## Shared Event Contracts

### `interaction_event.v1`

- emitted by `interaction-service`
- published to `interactions.events.v1`
- event types:
  - `impression`
  - `click`
  - `like`
  - `save`
  - `skip`
  - `watch_start`
  - `watch_complete`

### `ranking_decision.v1`

- emitted by `ranking-service`
- published to `ranking.decisions.v1`
- purpose: preserve ranking strategy, ordered results, and explainability metadata

### `dead_letter_event.v1`

- emitted by `feature-processor` on unrecoverable event processing failures
- published to `interactions.events.dlq.v1`

## Design Principles Reflected In The Model

- user and content domains remain simple and explicit
- immutable interaction storage creates a replay/debug boundary
- experiments are modeled as delivered exposures, not just user assignments
- low-latency Redis keys have durable PostgreSQL snapshot counterparts
- schema names and topic names are explicit and versioned
