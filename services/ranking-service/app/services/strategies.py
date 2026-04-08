"""Strategy registry for ranking-service scoring variants."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import config

from shared_schemas import (
    RULES_V1_RANKING_STRATEGY,
    RULES_V2_TRENDING_BOOST_RANKING_STRATEGY,
    SUPPORTED_RANKING_STRATEGIES,
)


@dataclass(frozen=True)
class StrategyDefinition:
    """Weights and adjustments used by a ranking strategy."""

    name: str
    user_topic_affinity_weight: float
    recency_weight: float
    engagement_weight: float
    trending_weight: float
    trending_boost_threshold: float = 1.0
    trending_boost_multiplier: float = 0.0
    max_strategy_adjustment: float = 0.0

    def compute_strategy_adjustment(self, normalized_trending: float) -> float:
        """Return the strategy-specific score adjustment for the candidate."""

        if normalized_trending <= self.trending_boost_threshold:
            return 0.0
        boost = (
            normalized_trending - self.trending_boost_threshold
        ) * self.trending_boost_multiplier
        return round(min(boost, self.max_strategy_adjustment), 6)


STRATEGY_DEFINITIONS = {
    RULES_V1_RANKING_STRATEGY: StrategyDefinition(
        name=RULES_V1_RANKING_STRATEGY,
        user_topic_affinity_weight=config.USER_TOPIC_AFFINITY_WEIGHT,
        recency_weight=config.RECENCY_WEIGHT,
        engagement_weight=config.ENGAGEMENT_WEIGHT,
        trending_weight=config.TRENDING_WEIGHT,
    ),
    RULES_V2_TRENDING_BOOST_RANKING_STRATEGY: StrategyDefinition(
        name=RULES_V2_TRENDING_BOOST_RANKING_STRATEGY,
        user_topic_affinity_weight=config.V2_USER_TOPIC_AFFINITY_WEIGHT,
        recency_weight=config.V2_RECENCY_WEIGHT,
        engagement_weight=config.V2_ENGAGEMENT_WEIGHT,
        trending_weight=config.V2_TRENDING_WEIGHT,
        trending_boost_threshold=config.V2_TRENDING_BOOST_THRESHOLD,
        trending_boost_multiplier=config.V2_TRENDING_BOOST_MULTIPLIER,
        max_strategy_adjustment=config.V2_MAX_STRATEGY_ADJUSTMENT,
    ),
}


def get_strategy_definition(strategy_name: str) -> StrategyDefinition:
    """Return the configured strategy definition for the provided strategy name."""

    normalized = strategy_name.strip()
    if normalized == "rules_based.v1":
        normalized = RULES_V1_RANKING_STRATEGY

    strategy = STRATEGY_DEFINITIONS.get(normalized)
    if strategy is None:
        raise ValueError(
            "Unsupported ranking strategy. Expected one of "
            f"{', '.join(SUPPORTED_RANKING_STRATEGIES)}"
        )
    return strategy
