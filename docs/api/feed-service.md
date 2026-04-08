# Feed Service API

Base URL: `http://localhost:8004/api/v1`

`feed-service` is the public personalized feed entry point. It retrieves candidates from multiple sources, reads feature-processor outputs from Redis, calls `ranking-service` for deterministic scoring, paginates the ranked result, and caches the page in Redis.

## Endpoint

### `GET /feed`

Query params:

- `user_id`: required UUID
- `limit`: optional, default `20`, max `100`
- `offset`: optional, default `0`

Example:

`GET /api/v1/feed?user_id=5f1a550d-0191-43c2-b25d-a7c5e2daa001&limit=20&offset=0`

Returns `200 OK`:

```json
{
  "schema_name": "feed_response.v1",
  "user_id": "5f1a550d-0191-43c2-b25d-a7c5e2daa001",
  "items": [
    {
      "content_id": "c1000000-0000-0000-0000-000000000001",
      "title": "Backend Scaling Patterns",
      "description": "Backend content",
      "topic": "backend",
      "category": "backend",
      "published_at": "2026-04-08T12:00:00Z",
      "candidate_sources": ["recent", "topic_affinity"],
      "user_topic_affinity": 0.91,
      "content_features": {
        "schema_name": "content_features.v1",
        "content_id": "c1000000-0000-0000-0000-000000000001",
        "topic": "backend",
        "window_hours": 24,
        "impressions": 120,
        "clicks": 35,
        "likes": 11,
        "saves": 5,
        "skip_count": 3,
        "watch_starts": 10,
        "watch_completes": 7,
        "ctr": 0.291667,
        "like_rate": 0.314286,
        "save_rate": 0.142857,
        "skip_rate": 0.025,
        "completion_rate": 0.7,
        "trending_score": 18.4,
        "last_event_at": "2026-04-08T11:58:00Z",
        "updated_at": "2026-04-08T11:58:05Z"
      },
      "rank": 1,
      "score": 0.674677,
      "score_breakdown": {
        "user_topic_affinity": 0.91,
        "user_topic_affinity_weighted": 0.3185,
        "recency": 0.999421,
        "recency_weighted": 0.199884,
        "engagement": 0.286667,
        "engagement_weighted": 0.071667,
        "trending": 0.423132,
        "trending_weighted": 0.084626,
        "diversity_penalty": 0.0,
        "final_score": 0.674677
      }
    }
  ],
  "total_candidates": 43,
  "limit": 20,
  "offset": 0,
  "has_more": true,
  "cache_hit": false,
  "generated_at": "2026-04-08T12:00:01Z"
}
```

## Candidate Retrieval

Current candidate sources:

- recent published content from `content-service`
- trending content from published content ordered by Redis `trending_score`
- topic-aligned content from the user’s strongest topic affinities

Candidate de-duplication rules:

- de-duplicate by `content_id`
- preserve all contributing `candidate_sources`
- attach `content_features.v1` and the effective `user_topic_affinity` before calling `ranking-service`

## Feature Inputs

Feed generation reads Redis keys produced by `feature-processor`:

- content features: `feature:content:{content_id}:v1`
- user affinity: `feature:user:{user_id}:topic-affinity:v1`

If runtime user affinity exists, `feed-service` blends:

- `70%` normalized runtime affinity
- `30%` persisted profile topic preferences from `user-service`

If runtime affinity is missing, persisted topic preferences are used directly.

## Pagination

Pagination is applied after ranking:

- rank the full candidate set
- slice `offset:offset+limit`
- return `has_more` based on the full ranked result count

This keeps page boundaries consistent with the global ranked order.

## Caching

Redis page cache key:

- `feed:user:{user_id}:limit:{limit}:offset:{offset}:v1`

Behavior:

- cache successful page responses
- default TTL: `60` seconds
- cache empty results as well to reduce repeat upstream work
- cached responses return `cache_hit: true`

## Error Strategy

- `422 Unprocessable Entity`: invalid query params
- `503 Service Unavailable`: upstream candidate retrieval or ranking dependency failed

The feed layer does not silently skip failed upstream ranking calls. If candidate retrieval or scoring fails, the request surfaces as `503`.
