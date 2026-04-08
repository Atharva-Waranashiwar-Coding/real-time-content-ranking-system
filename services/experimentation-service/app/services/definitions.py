"""Code-defined experiment configuration for experimentation-service."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import config

from shared_schemas import (
    HOME_FEED_RANKING_EXPERIMENT_KEY,
    RULES_V1_RANKING_STRATEGY,
    RULES_V2_TRENDING_BOOST_RANKING_STRATEGY,
)


@dataclass(frozen=True)
class ExperimentVariantDefinition:
    """A single configured experiment variant."""

    variant_key: str
    strategy_name: str
    allocation_basis_points: int


@dataclass(frozen=True)
class ExperimentDefinition:
    """Configured experiment definition used for deterministic assignment."""

    experiment_key: str
    variants: tuple[ExperimentVariantDefinition, ...]


ACTIVE_EXPERIMENTS = {
    HOME_FEED_RANKING_EXPERIMENT_KEY: ExperimentDefinition(
        experiment_key=HOME_FEED_RANKING_EXPERIMENT_KEY,
        variants=(
            ExperimentVariantDefinition(
                variant_key="control",
                strategy_name=RULES_V1_RANKING_STRATEGY,
                allocation_basis_points=5000,
            ),
            ExperimentVariantDefinition(
                variant_key="trending_boost",
                strategy_name=RULES_V2_TRENDING_BOOST_RANKING_STRATEGY,
                allocation_basis_points=5000,
            ),
        ),
    )
}


def get_active_experiment() -> ExperimentDefinition:
    """Return the currently active experiment definition."""

    experiment = ACTIVE_EXPERIMENTS.get(config.ACTIVE_EXPERIMENT_KEY)
    if experiment is None:
        raise RuntimeError(
            f"Active experiment '{config.ACTIVE_EXPERIMENT_KEY}' is not configured"
        )
    return experiment
