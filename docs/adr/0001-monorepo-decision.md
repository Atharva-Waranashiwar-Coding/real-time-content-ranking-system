# ADR-0001: Monorepo Architecture Decision

**Date**: April 7, 2026  
**Status**: Accepted  
**Context**: Structuring a distributed system with multiple backend services, a frontend, and shared packages  
**Decision**: Use a monorepo approach instead of multiple separate repositories  

## Background

The Real-Time Content Ranking System requires multiple backend services (User, Content, Interaction, Feed, Ranking, Feature Processor, etc.), a frontend application, and shared libraries. We needed to decide between:

1. **Monorepo** (single repository, multiple projects)
2. **Monolithic** (single codebase, deployed as one unit)
3. **Polyrepo** (separate repository per service)

## Decision

**We chose a monorepo** with logical separation of concerns for backend services, frontend, shared packages, and infrastructure.

## Repository Structure

```
real-time-content-ranking-system/
├── apps/                   # Frontend applications
│   └── web/               # Next.js/React frontend
├── services/              # Backend microservices (deployed independently)
│   ├── api-gateway/
│   ├── user-service/
│   ├── content-service/
│   ├── interaction-service/
│   ├── feed-service/
│   ├── ranking-service/
│   ├── experimentation-service/
│   ├── analytics-service/
│   └── feature-processor/
├── packages/              # Shared Python/JS packages
│   ├── shared-schemas/
│   ├── shared-config/
│   ├── shared-logging/
│   └── shared-clients/
├── infra/                 # Infrastructure and configuration
│   ├── docker/           # Docker Compose, Dockerfiles
│   ├── grafana/          # Grafana dashboards
│   └── prometheus/       # Prometheus configuration
├── docs/                 # Documentation and ADRs
├── scripts/              # Development utilities
└── .github/workflows/    # CI/CD pipelines
```

## Rationale

### Advantages

1. **Unified Version Control**
   - Single source of truth for all code
   - Easier to track cross-service dependencies
   - Atomic commits for coordinated changes

2. **Shared Code Reusability**
   - Common schemas, logging, and configuration in shared packages
   - DRY principle for utilities used across services
   - Easier to maintain consistency

3. **Simplified Development Setup**
   - Single infrastructure compose file plus source-run service scripts start the local stack
   - One CI/CD pipeline configuration
   - Easier onboarding for new developers

4. **Coordinated Releases**
   - Version services together when needed
   - Easier to manage breaking changes across services
   - Single deployment workflow

5. **Simplified Deployment**
   - All services tested together
   - Easier to track interactions between services during CI
   - Reduced deployment matrix complexity

### Disadvantages

1. **Large Repository Size** (Mitigated by sparse checkout)
2. **Potential Build Performance** (Mitigated by focused CI configuration)
3. **Team Scalability** (Works well up to ~50 developers with proper tooling)

## Trade-offs vs Alternatives

### vs Polyrepo
- **Monorepo**: Easier shared code, simpler setup
- **Polyrepo**: Better team isolation, independent deployment cycles

### vs Monolithic
- **Monorepo**: Multiple independent deployments still possible
- **Monolithic**: Single binary, simpler ops but tighter coupling

## Implementation Details

### Service Independence

Each service remains independently deployable:
- Own `requirements.txt` and dependencies
- Own `Dockerfile` for containerization
- Own tests and CI checks
- Services communicate via APIs and Kafka, not shared code

### Shared Code

Shared packages are minimal and focused:
- **shared-schemas**: Request/response DTOs, event schemas (Pydantic models)
- **shared-config**: Configuration management from environment variables
- **shared-logging**: Log formatting and setup
- **shared-clients**: HTTP and Kafka client factories

### CI/CD Strategy

- Linting and tests run on all code
- Each service builds independently
- Full integration tests in dedicated pipeline
- Docker images built for all services on push

## Future Considerations

### Scaling
If the team grows significantly (>50 developers), consider:
- **Micromonorepo**: Services in separate Git repos aggregated via workspace
- **Workspaces**: pnpm, yarn, or lerna for JavaScript monorepo scaling
- **Focused CI**: Only build/test services that changed

### Deployment
Current approach supports:
- Independent service deployments (docker build + push per service)
- Coordinated deployments (orchestrated by CI pipeline)
- Canary deployments (gradual rollout)

## Decision Log

| Date | Event | Note |
|------|-------|------|
| 2026-04-07 | Initial decision | Chose monorepo for simplified development |
| Future review | Revisit at scale | Evaluate polyrepo if team and service complexity outgrow the current workflow |

## References

- [Monorepo characteristics](https://monorepo.tools/)
- [Google Monorepo](https://cacm.acm.org/magazines/2016/7/204032-why-google-stores-billions-of-lines-of-code-in-a-single-repository/fulltext)
- [Plaid Engineering: Monorepo](https://plaid.com/blog/monorepo/)
