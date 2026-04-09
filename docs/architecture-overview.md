# Architecture Overview

## System Shape

The platform is a distributed content-ranking system with three major planes:

- request plane: feed generation, ranking, experimentation, and frontend interactions
- event plane: interaction ingestion, Kafka fan-out, stream aggregation, and dead-letter handling
- operational plane: metrics, structured logs, readiness/liveness, and local dashboards

The current web app calls service endpoints directly. `api-gateway` remains in the repository as a reserved shell for future routing and platform concerns, but it is not the main UI path today.

## High-Level Flow

1. The frontend requests a personalized feed from `feed-service`.
2. `feed-service` retrieves recent, trending, and topic-aligned candidates using `content-service`, user context, Redis features, and deterministic experiment assignment.
3. `ranking-service` scores the candidates and returns per-item explainability data.
4. `feed-service` records an experiment exposure and returns the assembled page.
5. Frontend actions such as `click`, `like`, `save`, `skip`, and watch events go to `interaction-service`.
6. `interaction-service` persists the event for audit/replay and publishes `interactions.events.v1`.
7. `feature-processor` consumes the topic, updates rolling aggregates, materializes Redis features, and persists snapshots to PostgreSQL.
8. `analytics-service` attributes outcomes back to the most recent prior exposure for experiment reporting.

## Service Responsibilities

| Service | Responsibility | Depends On |
| --- | --- | --- |
| `user-service` | user accounts, profiles, topic preferences | PostgreSQL |
| `content-service` | content items, tags, draft/published state | PostgreSQL |
| `interaction-service` | event validation, audit persistence, Kafka publication | PostgreSQL, Kafka |
| `feature-processor` | rolling feature aggregation and DLQ handling | Kafka, Redis, PostgreSQL |
| `ranking-service` | deterministic ranking and decision publication | Kafka |
| `feed-service` | candidate retrieval, ranking orchestration, caching, exposure logging | Redis, `user-service`, `content-service`, `ranking-service`, `experimentation-service` |
| `experimentation-service` | assignment and exposure persistence | PostgreSQL |
| `analytics-service` | experiment comparison metrics | PostgreSQL |
| `api-gateway` | reserved gateway shell | none |

## Data Boundaries

### PostgreSQL

Owns durable records for:

- users and user profiles
- content items and tags
- interaction audit events
- experiment assignments and exposures
- content feature snapshots
- user-topic feature snapshots

### Redis

Owns low-latency serving data for:

- `feature:content:{content_id}:v1`
- `feature:user:{user_id}:topic-affinity:v1`
- feed page cache entries

### Kafka

Owns asynchronous system flow for:

- `interactions.events.v1`
- `ranking.decisions.v1`
- `interactions.events.dlq.v1`

## Ranking Model

The ranking boundary is intentionally simple and replaceable.

Inputs:

- user topic affinity
- recency
- engagement rates
- trending score
- optional diversity penalty

Outputs:

- ordered candidate list
- numeric score
- per-factor score breakdown
- ranking decision event for downstream analysis

This allows the current rules engine to be replaced later by a trained model without changing the feed contract.

## Experimentation Model

- assignment is deterministic from a hash of `experiment_key:user_id`
- feed exposure rows are recorded when a page is actually delivered
- analytics attribute `click`, `save`, and `watch_complete` to the most recent prior exposure for the same `user_id` and `content_id`

This is more credible than assignment-only reporting because it measures the strategy that actually served the item.

## Operational Model

Telemetry currently includes:

- request count and latency by service
- ranking latency by strategy
- event publish and consume throughput
- feed assembly latency split by cache hit
- consumer lag where available
- structured logs with request and correlation IDs
- readiness and liveness endpoints
- dead-letter handling for failed event processing

Local monitoring assets live under `infra/docker/` and are documented in [observability.md](observability.md).

## Local Development Notes

- Docker Compose provisions infrastructure and monitoring, not the service processes.
- Services run from source using `bash scripts/run_service.sh <service-name>`.
- Demo state is intentionally bootstrapable and resettable with `bash scripts/setup_demo.sh`.
