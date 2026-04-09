# Repository Standards

## Monorepo Layout

The repository is organized by responsibility:

- `services/`: backend services
- `packages/`: shared schemas, clients, config, and logging helpers
- `apps/`: frontend applications
- `infra/`: Docker, Prometheus, Grafana, and environment bootstrap assets
- `docs/`: architecture, API, runbooks, demo notes, and interview notes
- `scripts/`: local utilities for running, seeding, linting, and formatting

## Naming Conventions

### Services and files

- service directories use `kebab-case`
- Python modules use `snake_case`
- classes use `PascalCase`
- constants use `UPPER_SNAKE_CASE`

### APIs

- all public endpoints are versioned under `/api/v1`
- request and response payloads are modeled with Pydantic
- route names should stay explicit rather than shortened

### Kafka topics and schema names

- topics use dotted lowercase versioning such as `interactions.events.v1`
- schema names are explicit and versioned such as `interaction_event.v1`

### Databases

- tables use plural `snake_case`
- foreign keys use `_id`
- timestamps use `_at`

## Code Style

### Python

- format with `black`
- lint with `ruff`
- keep public functions typed
- prefer explicit DTOs over loose dictionaries on service boundaries

### TypeScript

- keep API contracts typed
- prefer small reusable components over page-local ad hoc rendering
- avoid hardcoded fallback data unless it is clearly labeled demo-only data

## Testing

- backend tests live under each service in `tests/`
- frontend validation currently relies on TypeScript and production builds
- favor deterministic fixtures over random test data when ranking or analytics behavior is involved

## Documentation Rules

- README content should describe the current state of the repository, not an earlier phase plan
- use relative markdown links so docs render correctly on GitHub
- keep service names and topic names identical to the implementation

## Commit Style

Use conventional commits with a scope where it improves clarity:

- `feat(feed-service): add cached feed assembly`
- `docs(readme): rewrite setup and demo flow`
- `chore(repo): remove legacy scaffolding`
