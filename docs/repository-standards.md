# Repository Standards

This document defines the standards, conventions, and best practices for the Real-Time Content Ranking System repository.

## Directory Structure

All code follows the prescribed monorepo architecture defined in [ADR-0001](adr/0001-monorepo-decision.md):

```
services/          # Backend microservices
packages/          # Shared libraries and utilities
apps/              # Frontend applications
infra/             # Infrastructure and configuration
docs/              # Documentation
scripts/           # Utility scripts
tests/             # Shared tests
```

## Naming Conventions

### Branches

Use conventional branch naming for phase-based development:

```
phase/<number>-<short-name>
  phase/00-foundation-setup
  phase/01-core-domain-services
  phase/02-interaction-stream-ingestion
```

### Commits

Follow Conventional Commits format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat:` New feature
- `fix:` Bug fix
- `refactor:` Code refactoring
- `docs:` Documentation
- `test:` Tests
- `chore:` Maintenance
- `build:` Build configuration
- `perf:` Performance optimization
- `ci:` CI/CD configuration

**Examples:**
```
feat(user-service): add topic preference endpoints
fix(ranking-service): correct diversity penalty calculation
docs: update architecture overview
chore: update dependencies
build: add kafka consumer health check
```

### Python Naming

**Modules and packages:**
- `lowercase_with_underscores.py`

**Classes:**
- `PascalCase`

**Functions and methods:**
- `lowercase_with_underscores()`

**Constants:**
- `UPPER_CASE_WITH_UNDERSCORES`

**Files:**
- Service directories: `kebab-case` (e.g., `user-service`, `feature-processor`)
- Python files: `snake_case` (e.g., `config.py`, `health.py`)

### API Naming

**Endpoints:**
```
/api/v1/{resource}/{id}/{action}
  /api/v1/users
  /api/v1/users/{user_id}
  /api/v1/interactions
  /api/v1/feed?limit=20&offset=0
  /api/v1/content/{content_id}/related
```

**All endpoints are versioned** (v1 prefix) to enable backward compatibility.

### Kafka Topics

```
{domain}.{entity}.{version}
  interactions.events.v1
  user.features.v1
  content.features.v1
  ranking.decisions.v1
  experiments.exposures.v1
```

### Database

**Tables:**
- Snake case, pluralized
- Examples: `users`, `user_profiles`, `content_items`, `interactions`

**Columns:**
- Snake case
- Use `_at` suffix for timestamps: `created_at`, `updated_at`
- Use `_id` suffix for foreign keys: `user_id`, `content_id`

**Environment variables:**
- `UPPER_CASE_WITH_UNDERSCORES`
- Prefix with service/domain for clarity: `DB_HOST`, `KAFKA_BOOTSTRAP_SERVERS`

## Code Style

### Python

**Format:**
- Use **black** for code formatting (line length: 100)
- Use **ruff** for linting and import sorting
- Type hints on all functions

**Example:**
```python
def calculate_ranking_score(
    user_affinity: float,
    content_engagement: float,
    recency_hours: int,
) -> float:
    """Calculate composite ranking score."""
    return (
        0.5 * user_affinity
        + 0.3 * content_engagement
        + 0.2 * (1 / (1 + recency_hours))
    )
```

**Documentation:**
- Use docstrings for modules, classes, and public functions
- Follow NumPy/Google docstring style:

```python
def get_user_topics(user_id: str) -> List[str]:
    """Retrieve user topic interests.
    
    Args:
        user_id: Unique user identifier
    
    Returns:
        List of topic names user is interested in
    
    Raises:
        ValueError: If user_id is invalid
    """
```

### TypeScript/JavaScript

**Format:**
- Use **prettier** for code formatting
- Use **ESLint** (Next.js config) for linting
- Type everything with TypeScript

**Example:**
```typescript
interface FeedItem {
  contentId: string;
  title: string;
  score: number;
  scoreBreakdown: ScoreBreakdown;
}

async function getFeed(userId: string, limit: number = 20): Promise<FeedItem[]> {
  const response = await apiClient.get(`/api/v1/feed?user_id=${userId}&limit=${limit}`);
  return response.data;
}
```

### Comments

- Comments should explain **why**, not **what**
- Code should be self-documenting
- Avoid obvious comments

**Good:**
```python
# Cache for 5 minutes to balance freshness and query performance
cache_ttl = 300
```

**Avoid:**
```python
# Set cache TTL
cache_ttl = 300

# Increment counter
counter += 1
```

## Testing

**Python:**
- Use **pytest** for unit and integration tests
- Place tests in `tests/` directory parallel to `app/`
- Aim for >80% code coverage
- Use fixtures for common test setup

**TypeScript/Frontend:**
- Use **Jest** for component and utility testing
- Place tests next to files with `.test.ts` naming
- Use React Testing Library for component tests

**Running tests:**
```bash
# Python
pytest services/ packages/ -v --cov=services

# Frontend
cd apps/web && npm test
```

## Pre-commit Hooks

All developers must install pre-commit hooks before committing:

```bash
pre-commit install
```

Hooks validate:
- Black formatting
- Ruff linting and import sorting
- No trailing whitespace
- No large files
- No merge conflicts
- No secrets

## Continuous Integration

All pushes to `main` and `phase/*` branches trigger CI pipeline:

1. **Linting**: ruff and black checks
2. **Type checking**: mypy for Python
3. **Tests**: pytest with coverage
4. **Docker builds**: Verify all services build

See [.github/workflows/ci.yml](../.github/workflows/ci.yml) for full CI configuration.

## Documentation

**README files:**
- Root `README.md` (quick start, overview)
- Each service can have `README.md` with service-specific notes

**Architecture Documentation:**
- `docs/architecture-overview.md` for system design
- `docs/adr/` for architectural decision records (ADRs)
- API endpoint documentation in docstrings

**ADR Format:**
See [0001-monorepo-decision.md](adr/0001-monorepo-decision.md) for ADR template and format.

## Development Workflow

1. **Create feature branch**
   ```bash
   git checkout -b phase/00-foundation-setup
   ```

2. **Make changes** following standards above

3. **Run formatting**
   ```bash
   bash scripts/format.sh
   ```

4. **Verify linting**
   ```bash
   bash scripts/lint.sh
   ```

5. **Run tests** (when available)
   ```bash
   pytest tests/ -v
   ```

6. **Commit** with conventional message
   ```bash
   git commit -m "feat(ranking-service): add explainability payload"
   ```

7. **Push and create PR**
   ```bash
   git push origin phase/00-foundation-setup
   ```

8. **Respond to CI feedback** and review comments

9. **Merge** once CI passes and approved

## Local Development

### Setup

```bash
# Clone repo
git clone <repo-url>
cd real-time-content-ranking-system

# Start infrastructure
docker-compose -f infra/docker/docker-compose.yml up -d

# Install pre-commit hooks
pre-commit install

# Create .env from template
cp .env.example .env
```

### Running Services

**Each service independently:**
```bash
cd services/api-gateway
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app/main.py
```

**Or with Docker:**
```bash
docker-compose up api-gateway
```

### Frontend Development

```bash
cd apps/web
npm install
npm run dev
# Browse to http://localhost:3000
```

## Dependency Management

### Python

- Pin all dependencies in `requirements.txt`
- Use compatible release specifiers: `package>=1.0,<2.0`
- Update shared packages in `setup.py` when publishing

### JavaScript

- Use `package.json` with `npm` or `yarn`
- Pin major versions: `"next": "^14.0.0"`

## Error Handling

### Python

All errors should be structured with context:

```python
from shared_schemas import ErrorResponse

try:
    result = process_event(event)
except ProcessingError as e:
    logger.error(f"Event processing failed: {e.message}", extra={
        "event_id": event.id,
        "error_code": e.code,
    })
    raise
```

### API Responses

All error responses use standardized format from `shared-schemas.ErrorResponse`

## Security Best Practices

- Never commit secrets or `.env` files (use `.env.example`)
- Store credentials in environment variables
- Use strong validation on all inputs
- Log errors without exposing sensitive data
- Future: add authentication layer to all service-to-service communication

## References

- Python Style: [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Git Flow: [Conventional Commits](https://www.conventionalcommits.org/)
- API Design: [REST Best Practices](https://restfulapi.net/)
