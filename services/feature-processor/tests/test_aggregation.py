"""Tests for feature aggregation math."""

from datetime import timedelta

from app.services import (
    MetricCounts,
    build_content_feature_record,
    build_user_topic_affinity_record,
    compute_topic_affinity_score,
    compute_trending_score,
)

from shared_schemas import utc_now


def test_build_content_feature_record_computes_rates_and_trending():
    """Content feature vectors should expose stable counts and derived rates."""

    now = utc_now()
    counts = MetricCounts(
        impressions=100,
        clicks=25,
        likes=10,
        saves=5,
        skip_count=4,
        watch_starts=12,
        watch_completes=9,
        last_event_at=now,
    )

    feature = build_content_feature_record(
        content_id="content-1",
        topic="backend",
        counts=counts,
        window_hours=24,
        updated_at=now,
    )

    assert feature.ctr == 0.25
    assert feature.like_rate == 0.4
    assert feature.save_rate == 0.2
    assert feature.skip_rate == 0.04
    assert feature.completion_rate == 0.75
    assert feature.trending_score == compute_trending_score(counts, 24, now)


def test_compute_trending_score_decays_for_stale_content():
    """Trending score should decay when the last event is older."""

    stale_counts = MetricCounts(
        impressions=10,
        clicks=4,
        likes=2,
        saves=1,
        last_event_at=utc_now() - timedelta(hours=48),
    )
    fresh_counts = MetricCounts(
        impressions=10,
        clicks=4,
        likes=2,
        saves=1,
        last_event_at=utc_now(),
    )

    assert compute_trending_score(fresh_counts, 24) > compute_trending_score(
        stale_counts,
        24,
    )


def test_build_user_topic_affinity_record_uses_weighted_interactions():
    """Topic affinity should reflect weighted positive and negative signals."""

    counts = MetricCounts(
        clicks=2,
        likes=1,
        saves=1,
        skip_count=1,
        watch_starts=2,
        watch_completes=1,
        last_event_at=utc_now(),
    )

    feature = build_user_topic_affinity_record(
        user_id="user-1",
        topic="ai",
        counts=counts,
        window_hours=24,
    )

    assert feature.affinity_score == compute_topic_affinity_score(counts)
    assert feature.affinity_score > 0
