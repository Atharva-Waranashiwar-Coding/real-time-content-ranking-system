# User Service API

Base URL: `http://localhost:8001/api/v1`

## Endpoints

### `POST /users`

Create a user and its one-to-one profile.

```json
{
  "username": "alice_dev",
  "email": "alice@example.com",
  "profile": {
    "bio": "Platform-focused engineer learning ranking systems.",
    "topic_preferences": {
      "ai": 0.92,
      "backend": 0.68,
      "system-design": 0.81,
      "devops": 0.35,
      "interview-prep": 0.24
    }
  }
}
```

Returns `201 Created` with the created user and nested profile.

### `GET /users`

List users with pagination.

Query params:
- `skip`: integer, default `0`
- `limit`: integer, default `100`, max `1000`

### `GET /users/{user_id}`

Fetch a user by ID, including the nested profile.

### `PUT /users/{user_id}`

Update core account fields.

```json
{
  "username": "alice_platform",
  "email": "alice.platform@example.com"
}
```

At least one field is required.

### `GET /users/{user_id}/profile`

Fetch the user profile only.

### `PUT /users/{user_id}/profile`

Update profile metadata or clear `bio` by sending `null` or an empty string.

```json
{
  "bio": "Principal engineer focused on backend and AI systems.",
  "topic_preferences": {
    "ai": 0.9,
    "backend": 0.8,
    "system-design": 0.75,
    "devops": 0.4,
    "interview-prep": 0.3
  }
}
```

### `PUT /users/{user_id}/topics`

Replace topic preferences only.

```json
{
  "topic_preferences": {
    "ai": 0.95,
    "backend": 0.6,
    "system-design": 0.8,
    "devops": 0.5,
    "interview-prep": 0.2
  }
}
```

## Validation Rules

- `username`: 3-255 chars, alphanumeric plus `_` and `-`
- `email`: valid email format
- `bio`: max 500 chars
- `topic_preferences`: keys must be one of `ai`, `backend`, `system-design`, `devops`, `interview-prep`
- `topic_preferences` scores: numeric values in the `0.0` to `1.0` range

## Error Examples

Duplicate username or email:

```json
{
  "detail": "Email 'alice@example.com' already exists"
}
```

Missing resource:

```json
{
  "detail": "User 'missing-user-id' not found"
}
```
