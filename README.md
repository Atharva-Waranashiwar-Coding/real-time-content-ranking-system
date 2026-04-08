# Real-Time Content Ranking System

A distributed event-driven content ranking platform that ingests user interaction streams in real-time, computes dynamic user and content features, and serves personalized feeds with explainable ranking, experimentation support, and production-grade observability.

## Project Overview

This is a sophisticated, production-style system designed to:

- Ingest and process user interactions in real time via Kafka
- Compute user topic affinity and content engagement features using streaming aggregation
- Serve personalized feeds with deterministic ranking and explainability
- Support A/B experimentation with multiple ranking strategies
- Provide full observability with Prometheus metrics, Grafana dashboards, and structured logging

### Target Domain

**Tech Learning Feed** – a personalized content platform featuring system design posts, AI tutorials, backend engineering articles, DevOps explainers, and interview prep content.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js/React)                     │
│                    Feed UI | Analytics | Dashboards                 │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────┐
│                    API Gateway (FastAPI)                             │
│                   Routing | Authentication                           │
└──────┬───────────┬──────────────┬──────────────┬────────────────────┘
       │           │              │              │
   ┌───▼────┐ ┌───▼────┐ ┌──────▼────┐ ┌──────▼────┐
   │ Content │ │ User   │ │Interaction│ │Feed/Ranking
   │ Service │ │ Service│ │ Service   │ │ Services
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

## Core Services

### Backend Services

1. **API Gateway** – Entry point for frontend requests, routing to domain services
2. **User Service** – User profiles, topic preferences, account metadata
3. **Content Service** – Content metadata, categories, tags, publishing status
4. **Interaction Service** – Ingestion of interaction events, validation, Kafka publishing
5. **Feed Service** – Personalized feed endpoint, pagination, caching
6. **Ranking Service** – Rules-based ranking logic with score breakdown and explainability
7. **Feature Processor** – Stream processor consuming Kafka, computing features, materializing to Redis
8. **Analytics Service** – Aggregated dashboards and trend metrics
9. **Experimentation Service** – Experiment assignment, strategy variants, exposure logging

### Shared Packages

- **shared-schemas** – Common Pydantic models for events, DTOs, and validation
- **shared-config** – Centralized configuration and environment management
- **shared-logging** – Structured logging setup and utilities
- **shared-clients** – HTTP client factories and Kafka producer/consumer wrappers

### Infrastructure

- **PostgreSQL** – System of record for users, content, interactions, and features
- **Redis** – Low-latency feature lookup and feed caching
- **Kafka** – Event streaming with Zookeeper for coordination
- **Prometheus** – Metrics collection
- **Grafana** – Metrics visualization and dashboards
- **Runbooks** – Local monitoring and debugging workflows

## Tech Stack

### Backend
- Python 3.10+
- FastAPI
- SQLAlchemy + Alembic
- Pydantic
- Confluent Kafka / aiokafka
- Redis client

### Frontend
- Next.js / React 18+
- TypeScript
- Tailwind CSS
- Recharts / ECharts

### Data & Streaming
- Apache Kafka
- Zookeeper
- Python streaming workers (upgrade path to Flink/Spark)

### DevOps & Quality
- Docker + Docker Compose
- pytest
- ruff + black
- GitHub Actions CI
- Prometheus + Grafana

## Quick Start

### Prerequisites

- Docker and Docker Compose 2.0+
- Python 3.10+
- Node.js 18+ (for frontend)
- Git

### Local Development

1. **Clone and setup**
   ```bash
   git clone https://github.com/Atharva-Waranashiwar-Coding/real-time-content-ranking-system.git
   cd real-time-content-ranking-system
   ```

2. **Start the full stack**
   ```bash
   docker-compose -f infra/docker/docker-compose.yml up -d
   ```

   This spins up:
   - PostgreSQL (port 5432)
   - Redis (port 6379)
   - Kafka + Zookeeper (port 9092, 2181)
   - Prometheus (port 9090)
   - Grafana (port 3000)

3. **Install backend dependencies**
   ```bash
   cd services/api-gateway
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python app/main.py
   ```

4. **Install frontend dependencies**
   ```bash
   cd apps/web
   npm install
   npm run dev
   ```

5. **Access the system**
   - Frontend: http://localhost:3000
   - API Gateway: http://localhost:8000/health
   - Grafana: http://localhost:3000 (admin/admin)
   - Prometheus: http://localhost:9090

## Repository Structure

```
real-time-content-ranking-system/
├── apps/
│   └── web/                          # Next.js/React frontend
├── services/
│   ├── api-gateway/                  # FastAPI gateway
│   ├── user-service/                 # User domain service
│   ├── content-service/              # Content domain service
│   ├── interaction-service/          # Interaction ingestion
│   ├── feed-service/                 # Personalized feed endpoint
│   ├── ranking-service/              # Ranking engine
│   ├── experimentation-service/      # A/B experiment framework
│   ├── analytics-service/            # Analytics and metrics
│   └── feature-processor/            # Kafka stream processor
├── packages/
│   ├── shared-schemas/               # Common Pydantic models
│   ├── shared-config/                # Configuration utilities
│   ├── shared-logging/               # Logging and observability helpers
│   └── shared-clients/               # HTTP/Kafka clients
├── infra/
│   └── docker/                       # Docker Compose, Prometheus, Grafana, dashboards
├── docs/
│   ├── architecture-overview.md      # System design
│   ├── observability.md              # Telemetry and dashboard inventory
│   ├── repository-standards.md       # Code standards
│   ├── runbooks/                     # Local monitoring and debugging workflows
│   └── adr/                          # Architecture decision records
├── scripts/
│   ├── lint.sh                       # Linting automation
│   └── format.sh                     # Code formatting
├── .github/
│   └── workflows/                    # CI/CD pipelines
└── .editorconfig, .gitignore, pyproject.toml, package.json
```

## Naming Conventions

- **Branches:** `phase/<number>-<short-name>` (e.g., `phase/00-foundation-setup`)
- **Commits:** Conventional commits (`feat:`, `fix:`, `chore:`, `docs:`, `test:`, `build:`)
- **API paths:** `/api/v1/...` for versioned endpoints
- **Kafka topics:** lowercase with dots (e.g., `interactions.events.v1`)
- **Database tables:** snake_case pluralized (e.g., `user_profiles`, `content_items`)
- **Environment variables:** UPPER_SNAKE_CASE

## Development Workflow

### Code Quality

1. **Format code**
   ```bash
   bash scripts/format.sh
   ```

2. **Lint code**
   ```bash
   bash scripts/lint.sh
   ```

3. **Run tests**
   ```bash
   pytest tests/
   ```

### Pre-commit Hooks

Pre-commit hooks validate code before commit:
```bash
pre-commit install
```

Hooks include black, ruff, end-of-file-fixer, and trailing-whitespace.

## Phase-Based Implementation

- **Phase 0:** Foundation and monorepo setup (current)
- **Phase 1:** Core domain services (User, Content)
- **Phase 2:** Interaction ingestion and Kafka integration
- **Phase 3:** Feature aggregation pipeline
- **Phase 4:** Ranking engine and feed service
- **Phase 5:** Frontend UI and dashboards
- **Phase 6:** A/B experimentation framework
- **Phase 7:** Observability and hardening
- **Phase 8:** Demo readiness and polish

See [real_time_content_ranking_system_plan.md](real_time_content_ranking_system_plan.md) for detailed phase specifications.
See [docs/observability.md](docs/observability.md) for telemetry and dashboard details.
See [docs/runbooks/local-monitoring.md](docs/runbooks/local-monitoring.md) and [docs/runbooks/debugging.md](docs/runbooks/debugging.md) for local operations.

## Key Concepts

### Event-Driven Architecture
User interactions flow through Kafka topics, enabling decoupled, scalable processing of events across services.

### Real-Time Features
Feature Processor consumes interaction events and materializes aggregated signals to Redis for low-latency ranking queries.

### Personalized Ranking
Ranking Service computes scores based on user topic affinity, content trending, recency, and engagement with explainability payloads.

### Experimentation
Experimentation Service assigns users to ranking strategies and logs exposures for comparative analysis and winner determination.

## Contributing

Follow repository standards defined in [docs/repository-standards.md](docs/repository-standards.md).

## License

MIT License. See LICENSE file for details.

## Contact

For questions or feedback, reach out to [Atharva Waranashiwar](https://linkedin.com/in/atharva-waranashiwar).
