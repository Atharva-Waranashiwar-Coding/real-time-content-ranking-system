# Phase 1 API Documentation

## API Versioning

All Phase 1 APIs are versioned under `/api/v1/`.

## Standard Response Format

### Success Response

```json
{
  "data": {},
  "status": 200,
  "message": "Operation successful"
}
```

### Error Response

```json
{
  "detail": "Error description",
  "status_code": 400
}
```

---

## User Service APIs

### Base URL

```
http://localhost:8001/api/v1
```

### Endpoints

#### 1. Create User

**Request:**
```
POST /users
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com"
}
```

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john_doe",
  "email": "john@example.com",
  "created_at": "2026-04-07T19:00:00Z",
  "updated_at": "2026-04-07T19:00:00Z",
  "profile": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "bio": null,
    "topic_preferences": {},
    "created_at": "2026-04-07T19:00:00Z",
    "updated_at": "2026-04-07T19:00:00Z"
  }
}
```

**Errors:**
- `400`: Username or email already exists
- `422`: Validation error (invalid email format, short username)

---

#### 2. Get User

**Request:**
```
GET /users/{user_id}
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john_doe",
  "email": "john@example.com",
  "created_at": "2026-04-07T19:00:00Z",
  "updated_at": "2026-04-07T19:00:00Z",
  "profile": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "bio": "Software engineer",
    "topic_preferences": {
      "ai": 0.8,
      "backend": 0.9
    },
    "created_at": "2026-04-07T19:00:00Z",
    "updated_at": "2026-04-07T19:00:00Z"
  }
}
```

**Errors:**
- `404`: User not found

---

#### 3. Update User

**Request:**
```
PUT /users/{user_id}
Content-Type: application/json

{
  "email": "newemail@example.com"
}
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john_doe",
  "email": "newemail@example.com",
  "created_at": "2026-04-07T19:00:00Z",
  "updated_at": "2026-04-07T19:10:00Z",
  "profile": { ... }
}
```

**Errors:**
- `404`: User not found
- `400`: Email already exists

---

#### 4. Get User Profile

**Request:**
```
GET /users/{user_id}/profile
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "bio": "Senior backend engineer",
  "topic_preferences": {
    "backend": 0.95,
    "system-design": 0.85,
    "devops": 0.7
  },
  "created_at": "2026-04-07T19:00:00Z",
  "updated_at": "2026-04-07T19:05:00Z"
}
```

**Errors:**
- `404`: Profile not found

---

#### 5. Update User Profile

**Request:**
```
PUT /users/{user_id}/profile
Content-Type: application/json

{
  "bio": "Updated bio",
  "topic_preferences": {
    "backend": 0.8,
    "ai": 0.5
  }
}
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "bio": "Updated bio",
  "topic_preferences": {
    "backend": 0.8,
    "ai": 0.5
  },
  "created_at": "2026-04-07T19:00:00Z",
  "updated_at": "2026-04-07T19:15:00Z"
}
```

---

#### 6. Update Topic Preferences

**Request:**
```
PUT /users/{user_id}/topics
Content-Type: application/json

{
  "topic_preferences": {
    "ai": 0.9,
    "backend": 0.7,
    "system-design": 0.8,
    "devops": 0.4,
    "interview-prep": 0.6
  }
}
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "bio": "Senior engineer",
  "topic_preferences": {
    "ai": 0.9,
    "backend": 0.7,
    "system-design": 0.8,
    "devops": 0.4,
    "interview-prep": 0.6
  },
  "created_at": "2026-04-07T19:00:00Z",
  "updated_at": "2026-04-07T19:20:00Z"
}
```

---

#### 7. List Users

**Request:**
```
GET /users?skip=0&limit=100
```

**Response (200 OK):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "john_doe",
    "email": "john@example.com",
    "created_at": "2026-04-07T19:00:00Z",
    "updated_at": "2026-04-07T19:00:00Z",
    "profile": { ... }
  },
  ...
]
```

**Query Parameters:**
- `skip`: Offset for pagination (default: 0)
- `limit`: Number of results (default: 100, max: depends on config)

---

## Content Service APIs

### Base URL

```
http://localhost:8002/api/v1
```

### Endpoints

#### 1. Create Tag

**Request:**
```
POST /tags
Content-Type: application/json

{
  "name": "python",
  "description": "Python programming language"
}
```

**Response (201 Created):**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "name": "python",
  "description": "Python programming language",
  "created_at": "2026-04-07T19:00:00Z",
  "updated_at": "2026-04-07T19:00:00Z"
}
```

**Errors:**
- `400`: Tag name already exists
- `422`: Validation error

---

#### 2. List Tags

**Request:**
```
GET /tags?skip=0&limit=100
```

**Response (200 OK):**
```json
[
  {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "name": "python",
    "description": "Python programming language",
    "created_at": "2026-04-07T19:00:00Z",
    "updated_at": "2026-04-07T19:00:00Z"
  },
  ...
]
```

---

#### 3. Get Tag

**Request:**
```
GET /tags/{tag_id}
```

**Response (200 OK):**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "name": "python",
  "description": "Python programming language",
  "created_at": "2026-04-07T19:00:00Z",
  "updated_at": "2026-04-07T19:00:00Z"
}
```

**Errors:**
- `404`: Tag not found

---

#### 4. Create Content Item

**Request:**
```
POST /content
Content-Type: application/json

{
  "title": "Understanding Distributed Systems",
  "description": "A comprehensive guide to building distributed systems",
  "topic": "distributed-systems",
  "category": "system-design",
  "tag_ids": ["tag_id_1", "tag_id_2"]
}
```

**Response (201 Created):**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440000",
  "title": "Understanding Distributed Systems",
  "description": "A comprehensive guide to building distributed systems",
  "topic": "distributed-systems",
  "category": "system-design",
  "status": "draft",
  "view_count": 0,
  "engagement_metadata": {},
  "created_at": "2026-04-07T19:00:00Z",
  "published_at": null,
  "updated_at": "2026-04-07T19:00:00Z",
  "tags": [
    {
      "id": "tag_id_1",
      "name": "distributed",
      "description": null,
      "created_at": "2026-04-07T18:00:00Z",
      "updated_at": "2026-04-07T18:00:00Z"
    }
  ]
}
```

**Errors:**
- `400`: Invalid category or validation error
- `422`: Validation error

---

#### 5. Get Content Item

**Request:**
```
GET /content/{content_id}
```

**Response (200 OK):**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440000",
  "title": "Understanding Distributed Systems",
  "description": "A comprehensive guide to building distributed systems",
  "topic": "distributed-systems",
  "category": "system-design",
  "status": "published",
  "view_count": 125,
  "engagement_metadata": {
    "impressions": 500,
    "clicks": 125,
    "likes": 45,
    "saves": 30
  },
  "created_at": "2026-04-07T19:00:00Z",
  "published_at": "2026-04-07T19:05:00Z",
  "updated_at": "2026-04-07T19:05:00Z",
  "tags": [ ... ]
}
```

**Errors:**
- `404`: Content not found

---

#### 6. List Content Items

**Request:**
```
GET /content?skip=0&limit=100&category=system-design&status=published&topic=distributed
```

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440000",
      "title": "Understanding Distributed Systems",
      ...  
    }
  ],
  "total": 45,
  "skip": 0,
  "limit": 100
}
```

**Query Parameters:**
- `skip`: Offset for pagination (default: 0)
- `limit`: Number of results (default: 100, max: 1000)
- `category`: Filter by category (optional): ai, backend, system-design, devops, interview-prep
- `status`: Filter by status (optional): draft, published
- `topic`: Filter by topic (optional, case-sensitive)

---

#### 7. Update Content Item

**Request:**
```
PUT /content/{content_id}
Content-Type: application/json

{
  "title": "Updated title",
  "category": "system-design",
  "tag_ids": ["new_tag_id"]
}
```

**Response (200 OK):**
```json
{
  ...updated content...
}
```

**Errors:**
- `404`: Content not found
- `400`: Invalid category

---

#### 8. Publish Content Item

**Request:**
```
POST /content/{content_id}/publish
```

**Response (200 OK):**
```json
{
  ...
  "status": "published",
  "published_at": "2026-04-07T19:25:00Z",
  ...
}
```

**Errors:**
- `404`: Content not found

---

#### 9. Delete Content Item

**Request:**
```
DELETE /content/{content_id}
```

**Response (204 No Content):**
```
(empty body)
```

**Errors:**
- `404`: Content not found

---

## Common Patterns

### Pagination

Use `skip` and `limit` query parameters:
```
GET /users?skip=0&limit=20
GET /content?skip=20&limit=20
```

### Filtering

Use query parameters for filtering:
```
GET /content?category=ai&status=published
GET /users?skip=0&limit=50
```

### Error Handling

All errors follow the standard format:
```json
{
  "detail": "Error description",
  "status_code": 400,
  "timestamp": "2026-04-07T19:00:00Z"
}
```

### Status Codes

- `200`: OK
- `201`: Created
- `204`: No Content
- `400`: Bad Request
- `404`: Not Found
- `422`: Validation Error
- `500`: Internal Server Error

---

## Curl Examples

### Create a User

```bash
curl -X POST http://localhost:8001/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice_dev",
    "email": "alice@example.com"
  }'
```

### Get User Profile

```bash
USER_ID="550e8400-e29b-41d4-a716-446655440000"
curl http://localhost:8001/api/v1/users/$USER_ID/profile
```

### Update Topic Preferences

```bash
USER_ID="550e8400-e29b-41d4-a716-446655440000"
curl -X PUT http://localhost:8001/api/v1/users/$USER_ID/topics \
  -H "Content-Type: application/json" \
  -d '{
    "topic_preferences": {
      "ai": 0.9,
      "backend": 0.7,
      "system-design": 0.8
    }
  }'
```

### Create Content Item

```bash
curl -X POST http://localhost:8002/api/v1/content \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Introduction to Microservices",
    "description": "Learn how to build scalable microservices",
    "topic": "microservices",
    "category": "backend"
  }'
```

### List Published Content in AI Category

```bash
curl "http://localhost:8002/api/v1/content?category=ai&status=published"
```

---

## Testing

Use the provided Postman collection or curl commands above to test the APIs.
