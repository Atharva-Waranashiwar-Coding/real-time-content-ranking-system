# Ranking Service API

Base URL: `http://localhost:8005/api/v1`

`ranking-service` is an internal scoring service used by `feed-service`. It ranks candidate content items with deterministic, explicit strategy variants and publishes ranking decision events to Kafka topic `ranking.decisions.v1`.

## Endpoint

### `POST /rankings`

Rank a batch of candidates for a user.

```json
{
  "schema_name": "ranking_request.v1",
  "strategy_name": "rules_v1",
  "user_id": "5f1a550d-0191-43c2-b25d-a7c5e2daa001",
  "apply_diversity_penalty": true,
  "metadata": {
    "surface": "home_feed",
    "feed_limit": 20,
    "feed_offset": 0
  },
  "candidates": [
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
      }
    }
  ]
}
```

Returns `200 OK`:

```json
{
  "schema_name": "ranking_response.v1",
  "decision_id": "8db62169-ff6d-4f53-9a88-4fb6f033303c",
  "strategy_name": "rules_v1",
  "user_id": "5f1a550d-0191-43c2-b25d-a7c5e2daa001",
  "candidate_count": 1,
  "generated_at": "2026-04-08T12:00:01Z",
  "ranked_items": [
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
  ]
}
```

## Scoring Formula

Inputs used by the rules-based scorer:

- `user_topic_affinity`
- recency from `published_at`
- engagement score derived from `ctr`, `like_rate`, `save_rate`, `completion_rate`, `skip_rate`
- normalized `trending_score`
- optional diversity penalty based on already selected topics/categories

Supported strategies:

- `rules_v1`
- `rules_v2_with_trending_boost`

`rules_v1` weighted formula:

- user topic affinity: `0.35`
- recency: `0.20`
- engagement: `0.25`
- trending: `0.20`

`rules_v2_with_trending_boost` adjustments:

- weights shift toward trending-sensitive scoring
- a bounded `strategy_adjustment` is added for high normalized trending values
- score breakdowns include this adjustment explicitly

Diversity penalty is a post-score deduction:

- repeated topic penalty: `0.12` per prior item of the same topic
- repeated category penalty: `0.05` per prior item of the same category
- capped at `0.35`

## Explainability

Each ranked item returns:

- normalized input scores
- weighted component contributions
- `strategy_adjustment` when the strategy applies a bounded boost
- applied diversity penalty
- final score

This is the stable explainability payload consumed by `feed-service`.

## Event Publication

Kafka topic:

- `ranking.decisions.v1`

Event schema:

- `ranking_decision.v1`

Each successful ranking request publishes:

- `decision_id`
- `strategy_name`
- `user_id`
- ranked items with score breakdowns
- `request_id`
- `correlation_id`

## Error Strategy

- `422 Unprocessable Entity`: invalid ranking request payload
- `503 Service Unavailable`: ranking completed but Kafka decision event publication failed

If decision publication fails, the HTTP request returns `503` rather than silently dropping the event.
