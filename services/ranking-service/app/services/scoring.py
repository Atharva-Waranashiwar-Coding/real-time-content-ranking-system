"""Deterministic rules-based scoring for ranking-service."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone

from app.core.config import config
from app.services.strategies import StrategyDefinition, get_strategy_definition

from shared_schemas import (
    RULES_V1_RANKING_STRATEGY,
    RankedContentItemV1Schema,
    RankingCandidateV1Schema,
    RankingScoreBreakdownV1Schema,
    utc_now,
)


@dataclass(slots=True)
class CandidateScoreState:
    """Precomputed scoring state for a single ranking candidate."""

    candidate: RankingCandidateV1Schema
    breakdown: RankingScoreBreakdownV1Schema
    base_score: float


def clamp_score(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    """Clamp a numeric score into the configured range."""

    return max(minimum, min(maximum, value))


def resolve_scoring_time(now: datetime | None = None) -> datetime:
    """Resolve the timestamp used for recency scoring."""

    if now is not None:
        return now

    if config.RANKING_FIXED_NOW:
        fixed_now = datetime.fromisoformat(config.RANKING_FIXED_NOW.replace("Z", "+00:00"))
        if fixed_now.tzinfo is None or fixed_now.tzinfo.utcoffset(fixed_now) is None:
            return fixed_now.replace(tzinfo=timezone.utc)
        return fixed_now.astimezone(timezone.utc)

    return utc_now()


def compute_recency_score(
    published_at: datetime | None,
    now: datetime | None = None,
) -> float:
    """Compute a bounded recency score using a simple half-life style decay."""

    if published_at is None:
        return 0.0

    current_time = resolve_scoring_time(now)
    age_hours = max((current_time - published_at).total_seconds() / 3600, 0.0)
    return round(
        clamp_score(
            1.0 / (1.0 + (age_hours / max(config.RECENCY_HALFLIFE_HOURS, 1.0)))
        ),
        6,
    )


def compute_engagement_score(candidate: RankingCandidateV1Schema) -> float:
    """Compute a bounded engagement score from rolling feature rates."""

    feature = candidate.content_features
    engagement_score = (
        0.35 * feature.ctr
        + 0.2 * feature.like_rate
        + 0.2 * feature.save_rate
        + 0.2 * feature.completion_rate
        - 0.15 * feature.skip_rate
    )
    return round(clamp_score(engagement_score), 6)


def normalize_trending_score(raw_trending_score: float) -> float:
    """Normalize raw trending score into a bounded score contribution."""

    if raw_trending_score <= 0:
        return 0.0
    return round(
        clamp_score(
            raw_trending_score
            / (raw_trending_score + max(config.TRENDING_SCORE_SATURATION, 1.0))
        ),
        6,
    )


def compute_base_breakdown(
    candidate: RankingCandidateV1Schema,
    strategy: StrategyDefinition,
    now: datetime | None = None,
) -> RankingScoreBreakdownV1Schema:
    """Compute non-diversity components for a candidate."""

    user_topic_affinity = round(clamp_score(candidate.user_topic_affinity), 6)
    recency = compute_recency_score(candidate.published_at, now)
    engagement = compute_engagement_score(candidate)
    trending = normalize_trending_score(candidate.content_features.trending_score)
    strategy_adjustment = strategy.compute_strategy_adjustment(trending)

    user_topic_affinity_weighted = round(
        user_topic_affinity * strategy.user_topic_affinity_weight,
        6,
    )
    recency_weighted = round(recency * strategy.recency_weight, 6)
    engagement_weighted = round(engagement * strategy.engagement_weight, 6)
    trending_weighted = round(trending * strategy.trending_weight, 6)
    final_score = round(
        user_topic_affinity_weighted
        + recency_weighted
        + engagement_weighted
        + trending_weighted,
        6,
    )
    final_score = round(final_score + strategy_adjustment, 6)

    return RankingScoreBreakdownV1Schema(
        user_topic_affinity=user_topic_affinity,
        user_topic_affinity_weighted=user_topic_affinity_weighted,
        recency=recency,
        recency_weighted=recency_weighted,
        engagement=engagement,
        engagement_weighted=engagement_weighted,
        trending=trending,
        trending_weighted=trending_weighted,
        strategy_adjustment=strategy_adjustment,
        diversity_penalty=0.0,
        final_score=final_score,
    )


def compute_diversity_penalty(
    candidate: RankingCandidateV1Schema,
    selected_items: list[RankedContentItemV1Schema],
) -> float:
    """Compute a deterministic diversity penalty from already selected items."""

    if not selected_items:
        return 0.0

    topic_counts = Counter(item.topic for item in selected_items)
    category_counts = Counter(item.category for item in selected_items)
    penalty = (
        topic_counts.get(candidate.topic, 0) * config.DIVERSITY_TOPIC_PENALTY
        + category_counts.get(candidate.category, 0) * config.DIVERSITY_CATEGORY_PENALTY
    )
    return round(min(penalty, config.MAX_DIVERSITY_PENALTY), 6)


def rank_candidates(
    candidates: list[RankingCandidateV1Schema],
    *,
    strategy_name: str = RULES_V1_RANKING_STRATEGY,
    apply_diversity_penalty: bool,
    now: datetime | None = None,
) -> list[RankedContentItemV1Schema]:
    """Rank candidate items with a greedy diversity-aware ordering pass."""

    scoring_time = resolve_scoring_time(now)
    strategy = get_strategy_definition(strategy_name)
    remaining_candidates: list[CandidateScoreState] = []
    for candidate in candidates:
        breakdown = compute_base_breakdown(candidate, strategy, scoring_time)
        remaining_candidates.append(
            CandidateScoreState(
                candidate=candidate,
                breakdown=breakdown,
                base_score=breakdown.final_score,
            )
        )
    ranked_items: list[RankedContentItemV1Schema] = []

    while remaining_candidates:
        best_index = 0
        best_item: tuple[float, float, datetime | None, str] | None = None
        best_penalty = 0.0

        for index, score_state in enumerate(remaining_candidates):
            diversity_penalty = (
                compute_diversity_penalty(score_state.candidate, ranked_items)
                if apply_diversity_penalty
                else 0.0
            )
            final_score = round(score_state.base_score - diversity_penalty, 6)
            tie_breaker = (
                final_score,
                score_state.base_score,
                score_state.candidate.published_at
                or datetime.min.replace(tzinfo=timezone.utc),
                str(score_state.candidate.content_id),
            )
            if best_item is None or tie_breaker > best_item:
                best_item = tie_breaker
                best_index = index
                best_penalty = diversity_penalty

        selected_state = remaining_candidates.pop(best_index)
        score_breakdown = selected_state.breakdown.model_copy(
            update={
                "diversity_penalty": best_penalty,
                "final_score": round(selected_state.base_score - best_penalty, 6),
            }
        )
        ranked_items.append(
            RankedContentItemV1Schema(
                **selected_state.candidate.model_dump(mode="python"),
                rank=len(ranked_items) + 1,
                score=score_breakdown.final_score,
                score_breakdown=score_breakdown,
            )
        )

    return ranked_items


__all__ = [
    "clamp_score",
    "compute_base_breakdown",
    "compute_diversity_penalty",
    "compute_engagement_score",
    "compute_recency_score",
    "get_strategy_definition",
    "normalize_trending_score",
    "rank_candidates",
    "resolve_scoring_time",
]
