# Experimentation Service API

Base URL: `http://localhost:8006/api/v1`

`experimentation-service` owns deterministic user assignment for ranking experiments and persists feed exposure rows used for downstream analytics attribution.

## Endpoints

### `GET /experiments/assignment`

Return the active experiment assignment for a user. The assignment is deterministic and stable for a given `{experiment_key, user_id}` pair.

Query params:

- `user_id`: required UUID

Example response:

```json
{
  "schema_name": "experiment_assignment.v1",
  "experiment_key": "home_feed_ranking.v1",
  "variant_key": "control",
  "strategy_name": "rules_v1",
  "user_id": "5f1a550d-0191-43c2-b25d-a7c5e2daa001",
  "assignment_bucket": 1234,
  "assigned_at": "2026-04-08T12:00:00Z"
}
```

### `POST /experiments/exposures`

Persist a feed exposure after feed-service has actually returned ranked items to the user.

```json
{
  "schema_name": "experiment_exposure_create.v1",
  "experiment_key": "home_feed_ranking.v1",
  "variant_key": "control",
  "strategy_name": "rules_v1",
  "user_id": "5f1a550d-0191-43c2-b25d-a7c5e2daa001",
  "session_id": "web-session-001",
  "feed_limit": 20,
  "feed_offset": 0,
  "cache_hit": false,
  "generated_at": "2026-04-08T12:00:01Z",
  "items": [
    {
      "content_id": "c1000000-0000-0000-0000-000000000001",
      "rank": 1,
      "score": 0.674677,
      "topic": "backend",
      "category": "backend"
    }
  ]
}
```

Returns `201 Created`:

```json
{
  "schema_name": "experiment_exposure.v1",
  "exposure_id": "6cbf35a8-d48a-4f2f-a1b4-92d6ac8425c9",
  "experiment_key": "home_feed_ranking.v1",
  "variant_key": "control",
  "strategy_name": "rules_v1",
  "user_id": "5f1a550d-0191-43c2-b25d-a7c5e2daa001",
  "recorded_at": "2026-04-08T12:00:01Z"
}
```

## Assignment Model

Current active experiment:

- `home_feed_ranking.v1`

Current variants:

- `control` → `rules_v1`
- `trending_boost` → `rules_v2_with_trending_boost`

Assignment rules:

- compute a stable hash from `{experiment_key}:{user_id}`
- map the resulting `0..9999` bucket into the configured variant allocation ranges
- persist the resolved assignment for auditability and future config stability

## Exposure Model

Exposure logging happens on feed delivery, not on assignment lookup:

- one exposure header row per returned feed response
- one exposure item row per content item in that response
- cached responses still create new exposure rows

This keeps experiment attribution tied to what the user actually received.

## Error Strategy

- `422 Unprocessable Entity`: invalid query params or payload shape
- `400 Bad Request`: exposure payload does not match the stored assignment
