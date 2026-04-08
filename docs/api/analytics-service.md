# Analytics Service API

Base URL: `http://localhost:8007/api/v1`

`analytics-service` aggregates experiment outcomes by strategy by joining experiment exposure rows with persisted interaction audit events.

## Endpoint

### `GET /experiments/{experiment_key}/comparison`

Return experiment comparison metrics for the requested lookback window.

Query params:

- `lookback_hours`: optional integer, default `168`, max `8760`

Example:

`GET /api/v1/experiments/home_feed_ranking.v1/comparison?lookback_hours=168`

Returns `200 OK`:

```json
{
  "schema_name": "experiment_comparison.v1",
  "experiment_key": "home_feed_ranking.v1",
  "lookback_hours": 168,
  "strategies": [
    {
      "variant_key": "control",
      "strategy_name": "rules_v1",
      "exposure_requests": 24,
      "item_exposures": 240,
      "unique_users": 12,
      "clicks": 58,
      "saves": 19,
      "completions": 22,
      "ctr": 0.241667,
      "save_rate": 0.079167,
      "completion_rate": 0.091667
    },
    {
      "variant_key": "trending_boost",
      "strategy_name": "rules_v2_with_trending_boost",
      "exposure_requests": 25,
      "item_exposures": 250,
      "unique_users": 13,
      "clicks": 67,
      "saves": 17,
      "completions": 31,
      "ctr": 0.268,
      "save_rate": 0.068,
      "completion_rate": 0.124
    }
  ],
  "generated_at": "2026-04-08T12:05:00Z"
}
```

## Attribution Model

Analytics attribution rules:

- the denominator is item-level experiment exposure rows
- `click`, `save`, and `watch_complete` are the current tracked outcomes
- each interaction is attributed to the most recent prior exposure for the same `{user_id, content_id}`
- repeated events of the same type do not inflate the metric for a single exposure item

Current reported metrics:

- CTR = clicked exposure items / total exposure items
- save rate = saved exposure items / total exposure items
- completion rate = completed exposure items / total exposure items

## Error Strategy

- `422 Unprocessable Entity`: invalid `lookback_hours`
- empty experiments return `200 OK` with `strategies: []`
