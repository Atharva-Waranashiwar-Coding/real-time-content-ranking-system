# Architecture Overview

## System Design

The Real-Time Content Ranking System is a distributed, event-driven platform designed to ingest user interaction streams, compute feature signals in real time, and serve personalized content feeds with explainability and A/B experimentation support.

## Core Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                           │
│                    Feed | Analytics | Dashboards                     │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────┐
│                    API Gateway (FastAPI)                             │
│              Routing | CORS | Authentication (future)               │
└──────┬───────────┬──────────────┬──────────────┬────────────────────┘
       │           │              │              │
   ┌───▼────┐ ┌───▼────┐ ┌──────▼────┐ ┌──────▼────┐
   │Content │ │ User   │ │Interaction│ │Feed/Ranking
   │Service │ │Service │ │ Service   │ │ Services
   └────┬────┘ └────┬───┘ └──────┬────┘ └──────┬────┘
        └────────────┴────────────┴─────────────┘
                     │
        ┌────────────▼───────────────┐
        │     Kafka (Event Bus)      │
        │  interactions.events.v1    │
        │  user.features.v1          │
        │  content.features.v1       │
        │  ranking.decisions.v1      │
        └────────────┬───────────────┘
                     │
        ┌────────────▼──────────────────┐
        │ Feature Processor (Stream)    │
        │ Aggregations | Materialization│
        └────────────┬──────────────────┘
                     │
        ┌────────────▼──────────────────┐
        │  Redis | PostgreSQL           │
        │  (Features | Audit | Metrics) │
        └───────────────────────────────┘

Observability:  Prometheus | Grafana | Structured Logs
```

## Service Responsibilities

### Backend Services

1. **API Gateway** (Port 8000)
   - Entry point for all frontend requests
   - Routes requests to appropriate domain services
   - Handles CORS and request/response transformations
   - Future: authentication, rate limiting

2. **User Service** (Port 8001)
   - User profile management
   - Topic preferences and interests
   - Account metadata and settings
   - Provides user context for ranking

3. **Content Service** (Port 8002)
   - Content catalog management
   - Metadata, categories, tags
   - Publishing status and scheduling
   - Content quality signals

4. **Interaction Service** (Port 8003)
   - Ingestion endpoint for user interactions
   - Event validation and enrichment
   - Kafka publishing for event streaming
   - Audit trail persistence

5. **Feed Service** (Port 8004)
   - `GET /api/v1/feed` endpoint
   - Candidate retrieval and pagination
   - Works with Ranking Service for scoring
   - Caching and performance optimization

6. **Ranking Service** (Port 8005)
   - Core ranking algorithm
   - Rules-based scoring with explainability
   - Score breakdown computation
   - Strategy variants for experimentation

7. **Experimentation Service** (Port 8006)
   - User-to-strategy assignment
   - Experiment exposure logging
   - Metrics aggregation
   - A/B test winner analysis

8. **Analytics Service** (Port 8007)
   - Aggregated metrics and dashboards
   - Trending content analysis
   - User preference trends
   - Feed performance metrics

9. **Feature Processor** (Port 8008)
   - Stream consumer (Kafka)
   - Real-time aggregation
   - Feature materialization (Redis, PostgreSQL)
   - Handles user and content embeddings

### Shared Packages

- **shared-schemas**: Pydantic models for events, DTOs, and validation
- **shared-config**: Centralized configuration management
- **shared-logging**: Structured logging setup and utilities
- **shared-clients**: HTTP and Kafka client factories

## Data Flow

### Interaction Pipeline

```
User Action
   ↓
Frontend sends interaction event
   ↓
Interaction Service validates and enriches
   ↓
Events published to Kafka (interactions.events.v1)
   ↓
Feature Processor consumes and aggregates
   ↓
Features materialized to Redis and PostgreSQL
   ↓
Feed Service queries features for ranking
   ↓
Ranking Service computes scores
   ↓
Feed returned to frontend with explanations
```

## Data Models

### Core Entities

- `users`: User accounts
- `user_profiles`: Extended user metadata and preferences
- `content_items`: Content catalog
- `interactions`: User action audit log (immutable)
- `user_topic_scores`: Real-time affinity signals
- `content_feature_snapshots`: Periodic feature snapshots
- `experiment_assignments`: User-to-strategy mappings
- `ranking_decisions`: Ranking decision history

### Event Schemas

All events flowing through Kafka use standardized schemas defined in `shared-schemas`.

**Interaction Event:**
```json
{
  "event_id": "evt_001",
  "event_type": "like | click | save | skip | watch_start | watch_complete",
  "user_id": "usr_123",
  "content_id": "cnt_456",
  "session_id": "ses_789",
  "topic": "system-design",
  "watch_duration_seconds": 120,
  "event_timestamp": "2026-04-07T19:30:00Z",
  "metadata": {
    "surface": "home_feed",
    "device_type": "web"
  }
}
```

## Infrastructure

### Local Development (Docker Compose)

- **PostgreSQL 15**: System of record (port 5432)
- **Redis 7**: Cache and feature store (port 6379)
- **Kafka + Zookeeper**: Event streaming (ports 9092, 2181)
- **Prometheus**: Metrics collection (port 9090)
- **Grafana**: Visualization (port 3000)

### Network

All services communicate over `ranking_network` bridge, enabling service discovery by hostname.

## Observability

### Metrics

All services export Prometheus metrics at `/metrics` endpoint. Key metrics include:
- Request count and latency
- Event throughput
- Feature computation time
- Redis cache hit rates

### Logging

Structured JSON logging with correlation IDs enables distributed tracing.

### Grafana Dashboards

- Feed latency and throughput
- Event ingestion rate
- Feature freshness
- Experiment performance comparison

## Reliability & Resilience

### Current Phase

- Health checks on all services
- Kafka auto-creates topics with replication
- Redis persistence enabled

### Future Phases

- Retry and backoff strategies
- Dead letter topic for failed events
- Circuit breakers for inter-service calls
- Graceful degradation

## Security (Future)

- Authentication layer in API Gateway
- Authorization per service
- Encryption in transit (TLS)
- Secret management for credentials

## Technology Stack Summary

| Layer | Technology |
|-------|------------|
| Frontend | Next.js, React 18, TypeScript, Tailwind CSS |
| API | FastAPI, SQLAlchemy, Pydantic |
| Database | PostgreSQL, Redis |
| Streaming | Apache Kafka, Zookeeper |
| Monitoring | Prometheus, Grafana |
| Infrastructure | Docker, Docker Compose |
| Quality | pytest, black, ruff, GitHub Actions CI |

## Deployment Strategy

**Phase 0 (Current)**: Local Docker Compose development environment

**Phase 7**: Production hardening and observability

**Phase 8**: Optional: Cloud deployment (AWS/Azure/GCP)

## References

- See [repository-standards.md](repository-standards.md) for development standards
- See ADRs in [docs/adr/](adr/) for architectural decisions
- See [../README.md](../README.md) for quick start
