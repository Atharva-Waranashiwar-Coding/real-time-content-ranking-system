# Core Domain APIs

This directory documents the Phase 1 domain APIs implemented by `user-service` and `content-service`.

## Conventions

- All endpoints are versioned under `/api/v1`.
- Request and response payloads use Pydantic schemas.
- Validation failures return `422 Unprocessable Entity`.
- Domain validation and duplicate-data failures return `400 Bad Request`.
- Missing resources return `404 Not Found`.

## Service Docs

- [user-service.md](/Users/atharvawaranashiwar/Documents/Projects/content_ranking_system/docs/api/user-service.md)
- [content-service.md](/Users/atharvawaranashiwar/Documents/Projects/content_ranking_system/docs/api/content-service.md)
