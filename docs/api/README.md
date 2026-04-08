# Core Domain APIs

This directory documents the domain APIs implemented by the backend services currently wired in the monorepo.

## Conventions

- All endpoints are versioned under `/api/v1`.
- Request and response payloads use Pydantic schemas.
- Validation failures return `422 Unprocessable Entity`.
- Domain validation and duplicate-data failures return `400 Bad Request`.
- Missing resources return `404 Not Found`.
- Interaction ingestion also uses `409 Conflict` for duplicate event IDs and `503 Service Unavailable` when Kafka publication fails after audit persistence.

## Service Docs

- [user-service.md](/Users/atharvawaranashiwar/Documents/Projects/content_ranking_system/docs/api/user-service.md)
- [content-service.md](/Users/atharvawaranashiwar/Documents/Projects/content_ranking_system/docs/api/content-service.md)
- [interaction-service.md](/Users/atharvawaranashiwar/Documents/Projects/content_ranking_system/docs/api/interaction-service.md)
- [ranking-service.md](/Users/atharvawaranashiwar/Documents/Projects/content_ranking_system/docs/api/ranking-service.md)
- [feed-service.md](/Users/atharvawaranashiwar/Documents/Projects/content_ranking_system/docs/api/feed-service.md)
- [feature-processor.md](/Users/atharvawaranashiwar/Documents/Projects/content_ranking_system/docs/api/feature-processor.md)
- [experimentation-service.md](/Users/atharvawaranashiwar/Documents/Projects/content_ranking_system/docs/api/experimentation-service.md)
- [analytics-service.md](/Users/atharvawaranashiwar/Documents/Projects/content_ranking_system/docs/api/analytics-service.md)
