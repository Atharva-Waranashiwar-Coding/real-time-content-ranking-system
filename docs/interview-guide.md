# Interview Guide

This project is designed to support both a product demo and a systems-design discussion. Use this guide to keep the explanation focused and credible.

## 60-Second Version

This is a distributed content-ranking platform for a technical learning feed. User interactions are accepted through an ingestion service, persisted for audit, published to Kafka, aggregated into low-latency feature vectors in Redis, and consumed by a feed pipeline that retrieves candidates, ranks them with an explainable rules-based scorer, records experiment exposures, and exposes comparison analytics. The frontend is intentionally built to make that system visible instead of abstracting it away.

## 5-Minute Walkthrough

1. Start with the domain.
   Explain that the product models a personalized engineering-learning feed across AI, backend, system design, DevOps, and interview preparation.

2. Show the feed path.
   `feed-service` retrieves recent, trending, and topic-aligned candidates, then calls `ranking-service`.

3. Explain the ranking contract.
   The scorer uses explicit inputs: user topic affinity, recency, engagement, trending score, and diversity penalty. Every ranked item returns a score breakdown.

4. Explain the event path.
   `interaction-service` validates an event against a shared schema, stores it in PostgreSQL for replay/audit, and publishes `interactions.events.v1`.

5. Explain the feature path.
   `feature-processor` consumes the Kafka topic, updates rolling metrics, materializes Redis features, and writes PostgreSQL snapshots.

6. Explain experimentation.
   Users are deterministically assigned to strategies. Feed exposures are persisted, and `analytics-service` attributes clicks, saves, and completions back to the most recent prior exposure.

7. Close with operations.
   Prometheus, Grafana, structured logging, readiness/liveness, retries, and dead-letter handling are all wired into the platform.

## Questions To Expect

### Why rules-based ranking first?

Because it makes the system explainable, testable, and demoable from day one. The ranking boundary is isolated behind explicit DTOs so a learned model can replace the scorer later without rewriting feed assembly or the frontend contract.

### Why Redis plus PostgreSQL?

Redis is the low-latency serving layer for ranking inputs and feed caches. PostgreSQL is the durable system of record for user/content domains, interaction audit logs, experiment data, and feature snapshots.

### Why Kafka here?

Kafka decouples ingestion from feature computation and creates a replayable event boundary. That makes feature processing operationally safer and lets the ingestion path stay simple.

### Why does the frontend call services directly?

Because the current demo optimizes for visibility and explicit contracts. The gateway exists in the repo, but the web app currently uses direct service URLs so each service remains visibly testable during the demo.

### What is actually production-oriented versus intentionally simplified?

Production-oriented:

- versioned schemas and topics
- structured logging and correlation IDs
- DLQ strategy for failed event processing
- explainable ranking outputs
- deterministic experiment assignment
- readiness, liveness, Prometheus, Grafana

Intentionally simplified:

- no authentication or authorization layer yet
- one Kafka consumer process instead of a more elastic streaming runtime
- deterministic rules-based scoring instead of a trained ranking model
- frontend talks directly to services instead of routing everything through a gateway/BFF

## Files Worth Referencing In An Interview

- `services/feed-service/app/services/feed_service.py`
- `services/feed-service/app/services/candidate_service.py`
- `services/ranking-service/app/services/scoring.py`
- `services/interaction-service/app/services/interaction_service.py`
- `services/feature-processor/app/services/feature_processor.py`
- `services/experimentation-service/app/services/experiment_service.py`
- `services/analytics-service/app/services/analytics_service.py`
- `packages/shared-schemas/__init__.py`

## Strong Talking Points

- The system has clear event boundaries and explicit versioning.
- The ranking logic is isolated and replaceable.
- The demo uses deterministic seed data instead of hand-waved mock state.
- Analytics are exposure-based, not just assignment-based, which is the right attribution model.
- Operational concerns were treated as first-class features rather than postponed.
