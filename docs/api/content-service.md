# Content Service API

Base URL: `http://localhost:8002/api/v1`

## Tag Endpoints

### `POST /tags`

Create a content tag.

```json
{
  "name": "distributed-systems",
  "description": "Distributed systems and scalability concepts"
}
```

### `GET /tags`

List tags with pagination.

Query params:
- `skip`: integer, default `0`
- `limit`: integer, default `100`, max `1000`

### `GET /tags/{tag_id}`

Fetch a tag by ID.

## Content Endpoints

### `POST /content`

Create a content item. New items default to `draft`, but `published` is also supported.

```json
{
  "title": "REST API Design Patterns",
  "description": "Building scalable HTTP APIs",
  "topic": "backend",
  "category": "backend",
  "status": "draft",
  "tag_ids": [
    "f7c0bb4f-1e5d-4d56-97c2-3a9b9d7d1010"
  ]
}
```

If `status` is `published`, the service sets `published_at`.

### `GET /content`

List content items with pagination and filtering.

Query params:
- `skip`: integer, default `0`
- `limit`: integer, default `100`, max `1000`
- `category`: `ai | backend | system-design | devops | interview-prep`
- `status`: `draft | published`
- `topic`: free-form topic slug
- `tag`: tag name

### `GET /content/{content_id}`

Fetch a single content item by ID.

### `PUT /content/{content_id}`

Update content metadata, tags, or status.

```json
{
  "description": "Updated overview of scalable API design",
  "status": "published",
  "tag_ids": [
    "f7c0bb4f-1e5d-4d56-97c2-3a9b9d7d1010",
    "63f24213-d7ef-4c6d-93fe-2b90c7db7d4b"
  ]
}
```

At least one field is required.

### `POST /content/{content_id}/publish`

Explicitly transition a content item to `published`.

### `DELETE /content/{content_id}`

Delete a content item.

## Validation Rules

- `title`: 5-500 chars
- `description`: max 2000 chars
- `topic`: 1-100 chars, normalized to lowercase
- `category`: one of `ai`, `backend`, `system-design`, `devops`, `interview-prep`
- `status`: `draft` or `published`
- `tag_ids`: every referenced tag ID must exist

## Error Examples

Unknown tag IDs:

```json
{
  "detail": "Unknown tag IDs: missing-tag-id"
}
```

Missing resource:

```json
{
  "detail": "Content 'missing-content-id' not found"
}
```
