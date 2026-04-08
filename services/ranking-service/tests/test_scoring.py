"""Tests for deterministic ranking score calculation."""

from datetime import timedelta
from uuid import uuid4

from app.services import (
    compute_diversity_penalty,
    compute_engagement_score,
    compute_recency_score,
    rank_candidates,
)

from shared_schemas import ContentFeaturesV1Schema, RankingCandidateV1Schema, utc_now


def _build_candidate(
    *,
    topic: str = "backend",
    category: str = "backend",
    user_topic_affinity: float = 0.5,
    published_at=None,
    ctr: float = 0.0,
    like_rate: float = 0.0,
    save_rate: float = 0.0,
    completion_rate: float = 0.0,
    skip_rate: float = 0.0,
    trending_score: float = 0.0,
) -> RankingCandidateV1Schema:
    """Create a ranking candidate with explicit feature inputs."""

    content_id = uuid4()
    return RankingCandidateV1Schema(
        content_id=content_id,
        title=f"Candidate {content_id}",
        description="Candidate content",
        topic=topic,
        category=category,
        published_at=published_at or utc_now(),
        candidate_sources=["recent"],
        user_topic_affinity=user_topic_affinity,
        content_features=ContentFeaturesV1Schema(
            content_id=content_id,
            topic=topic,
            ctr=ctr,
            like_rate=like_rate,
            save_rate=save_rate,
            completion_rate=completion_rate,
            skip_rate=skip_rate,
            trending_score=trending_score,
        ),
    )


def test_compute_recency_score_prefers_fresh_content():
    """Fresh content should receive a higher recency score."""

    fresh = utc_now()
    stale = fresh - timedelta(days=7)

    assert compute_recency_score(fresh, fresh) > compute_recency_score(stale, fresh)


def test_compute_engagement_score_clamps_to_zero_for_negative_mix():
    """Negative skip-heavy engagement should not produce a negative score."""

    candidate = _build_candidate(
        ctr=0.1,
        like_rate=0.0,
        save_rate=0.0,
        completion_rate=0.0,
        skip_rate=1.0,
    )

    assert compute_engagement_score(candidate) == 0.0


def test_rank_candidates_orders_by_composite_score():
    """Candidates should be ordered by the deterministic composite formula."""

    high_signal = _build_candidate(
        user_topic_affinity=0.9,
        ctr=0.6,
        like_rate=0.5,
        save_rate=0.3,
        completion_rate=0.4,
        trending_score=18.0,
    )
    lower_signal = _build_candidate(
        user_topic_affinity=0.2,
        ctr=0.1,
        like_rate=0.05,
        save_rate=0.0,
        completion_rate=0.1,
        trending_score=1.0,
    )

    ranked_items = rank_candidates(
        [lower_signal, high_signal],
        strategy_name="rules_v1",
        apply_diversity_penalty=False,
        now=utc_now(),
    )

    assert ranked_items[0].content_id == high_signal.content_id
    assert ranked_items[0].score > ranked_items[1].score


def test_diversity_penalty_reorders_repeated_topics():
    """Repeated topics should be penalized when diversity is enabled."""

    first_backend = _build_candidate(
        topic="backend",
        category="backend",
        user_topic_affinity=0.9,
        trending_score=12.0,
    )
    second_backend = _build_candidate(
        topic="backend",
        category="backend",
        user_topic_affinity=0.88,
        trending_score=11.5,
    )
    ai_candidate = _build_candidate(
        topic="ai",
        category="ai",
        user_topic_affinity=0.75,
        trending_score=10.0,
    )

    ranked_items = rank_candidates(
        [first_backend, second_backend, ai_candidate],
        strategy_name="rules_v1",
        apply_diversity_penalty=True,
        now=utc_now(),
    )

    assert ranked_items[0].topic == "backend"
    assert ranked_items[1].topic == "ai"
    assert ranked_items[2].score_breakdown.diversity_penalty > 0
    assert compute_diversity_penalty(second_backend, [ranked_items[0]]) > 0


def test_trending_boost_strategy_can_change_ordering():
    """High-trending content should benefit from the v2 strategy adjustment."""

    trending_candidate = _build_candidate(
        topic="backend",
        category="backend",
        user_topic_affinity=0.48,
        ctr=0.2,
        like_rate=0.12,
        save_rate=0.08,
        completion_rate=0.2,
        trending_score=15.0,
    )
    affinity_candidate = _build_candidate(
        topic="ai",
        category="ai",
        user_topic_affinity=0.68,
        ctr=0.2,
        like_rate=0.12,
        save_rate=0.08,
        completion_rate=0.2,
        trending_score=1.0,
    )

    ranked_v1 = rank_candidates(
        [affinity_candidate, trending_candidate],
        strategy_name="rules_v1",
        apply_diversity_penalty=False,
        now=utc_now(),
    )
    ranked_v2 = rank_candidates(
        [affinity_candidate, trending_candidate],
        strategy_name="rules_v2_with_trending_boost",
        apply_diversity_penalty=False,
        now=utc_now(),
    )

    assert ranked_v1[0].content_id == affinity_candidate.content_id
    assert ranked_v2[0].content_id == trending_candidate.content_id
