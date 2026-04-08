"""Aggregation logic for experiment outcome analytics."""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app.core import RequestContext, config
from app.models import ExperimentExposure, Interaction
from app.schemas import ExperimentComparisonResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import select

from shared_schemas import StrategyOutcomeMetricsV1Schema, utc_now

logger = logging.getLogger(config.SERVICE_NAME)


@dataclass
class AttributedExposureItem:
    """In-memory experiment exposure item used for interaction attribution."""

    item_id: str
    generated_at: datetime
    strategy_name: str
    variant_key: str
    user_id: str
    clicked: bool = False
    saved: bool = False
    completed: bool = False


@dataclass
class StrategyAccumulator:
    """Mutable accumulator for per-strategy experiment metrics."""

    variant_key: str
    strategy_name: str
    exposure_requests: int = 0
    item_exposures: int = 0
    clicks: int = 0
    saves: int = 0
    completions: int = 0
    unique_users: set[str] = field(default_factory=set)


class AnalyticsService:
    """Service for aggregating experiment comparison metrics."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_experiment_comparison(
        self,
        experiment_key: str,
        lookback_hours: int,
        request_context: RequestContext,
    ) -> ExperimentComparisonResponse:
        """Return comparison metrics for a ranking experiment."""

        cutoff = utc_now() - timedelta(hours=lookback_hours)
        exposures_query = (
            select(ExperimentExposure)
            .options(selectinload(ExperimentExposure.items))
            .where(
                ExperimentExposure.experiment_key == experiment_key,
                ExperimentExposure.created_at >= cutoff,
            )
        )
        exposures_result = await self.session.execute(exposures_query)
        exposures = exposures_result.scalars().unique().all()

        if not exposures:
            return ExperimentComparisonResponse(
                experiment_key=experiment_key,
                lookback_hours=lookback_hours,
                strategies=[],
            )

        (
            strategy_accumulators,
            attribution_index,
            min_generated_at,
            content_ids,
            user_ids,
        ) = self._build_exposure_state(exposures)
        interactions = await self._load_candidate_interactions(
            user_ids=user_ids,
            content_ids=content_ids,
            min_generated_at=min_generated_at,
        )
        attributed_items = self._attribute_interactions(attribution_index, interactions)
        self._apply_outcome_counts(strategy_accumulators, attributed_items)
        strategy_metrics = self._build_strategy_metrics(strategy_accumulators)

        logger.info(
            "Experiment comparison generated",
            extra={
                **request_context.to_log_fields(),
                "experiment_key": experiment_key,
                "lookback_hours": lookback_hours,
                "strategy_count": len(strategy_metrics),
            },
        )

        return ExperimentComparisonResponse(
            experiment_key=experiment_key,
            lookback_hours=lookback_hours,
            strategies=strategy_metrics,
        )

    @staticmethod
    def _build_exposure_state(
        exposures: list[ExperimentExposure],
    ) -> tuple[
        dict[str, StrategyAccumulator],
        dict[tuple[str, str], list[AttributedExposureItem]],
        datetime,
        set[str],
        set[str],
    ]:
        """Build in-memory attribution state from persisted exposure rows."""

        strategy_accumulators: dict[str, StrategyAccumulator] = {}
        attribution_index: dict[tuple[str, str], list[AttributedExposureItem]] = defaultdict(list)
        min_generated_at = min(exposure.generated_at for exposure in exposures)
        content_ids: set[str] = set()
        user_ids: set[str] = set()

        for exposure in exposures:
            accumulator = strategy_accumulators.setdefault(
                exposure.strategy_name,
                StrategyAccumulator(
                    variant_key=exposure.variant_key,
                    strategy_name=exposure.strategy_name,
                ),
            )
            accumulator.exposure_requests += 1
            accumulator.unique_users.add(exposure.user_id)
            user_ids.add(exposure.user_id)

            for item in exposure.items:
                accumulator.item_exposures += 1
                content_ids.add(item.content_id)
                attribution_index[(exposure.user_id, item.content_id)].append(
                    AttributedExposureItem(
                        item_id=item.id,
                        generated_at=exposure.generated_at,
                        strategy_name=exposure.strategy_name,
                        variant_key=exposure.variant_key,
                        user_id=exposure.user_id,
                    )
                )

        for exposure_items in attribution_index.values():
            exposure_items.sort(key=lambda item: item.generated_at, reverse=True)

        return (
            strategy_accumulators,
            attribution_index,
            min_generated_at,
            content_ids,
            user_ids,
        )

    async def _load_candidate_interactions(
        self,
        *,
        user_ids: set[str],
        content_ids: set[str],
        min_generated_at: datetime,
    ) -> list[Interaction]:
        """Load interactions that can affect the requested comparison window."""

        interactions_query = select(Interaction).where(
            Interaction.user_id.in_(sorted(user_ids)),
            Interaction.content_id.in_(sorted(content_ids)),
            Interaction.event_type.in_(["click", "save", "watch_complete"]),
            Interaction.event_timestamp >= min_generated_at,
        )
        interactions_result = await self.session.execute(interactions_query)
        return interactions_result.scalars().all()

    @staticmethod
    def _attribute_interactions(
        attribution_index: dict[tuple[str, str], list[AttributedExposureItem]],
        interactions: list[Interaction],
    ) -> list[AttributedExposureItem]:
        """Attribute outcome events to the most recent prior exposure item."""

        attributed_items_by_id = {
            item.item_id: item
            for items in attribution_index.values()
            for item in items
        }

        for interaction in sorted(interactions, key=lambda item: item.event_timestamp):
            candidate_items = attribution_index.get(
                (interaction.user_id, interaction.content_id),
                [],
            )
            matched_item = next(
                (
                    item
                    for item in candidate_items
                    if item.generated_at <= interaction.event_timestamp
                ),
                None,
            )
            if matched_item is None:
                continue
            if interaction.event_type == "click":
                matched_item.clicked = True
            elif interaction.event_type == "save":
                matched_item.saved = True
            elif interaction.event_type == "watch_complete":
                matched_item.completed = True

        return list(attributed_items_by_id.values())

    @staticmethod
    def _apply_outcome_counts(
        strategy_accumulators: dict[str, StrategyAccumulator],
        attributed_items: list[AttributedExposureItem],
    ) -> None:
        """Update per-strategy counters from attributed exposure outcomes."""

        for attributed_item in attributed_items:
            accumulator = strategy_accumulators[attributed_item.strategy_name]
            if attributed_item.clicked:
                accumulator.clicks += 1
            if attributed_item.saved:
                accumulator.saves += 1
            if attributed_item.completed:
                accumulator.completions += 1

    @staticmethod
    def _build_strategy_metrics(
        strategy_accumulators: dict[str, StrategyAccumulator],
    ) -> list[StrategyOutcomeMetricsV1Schema]:
        """Convert mutable accumulators into response DTOs."""

        return [
            StrategyOutcomeMetricsV1Schema(
                variant_key=accumulator.variant_key,
                strategy_name=accumulator.strategy_name,
                exposure_requests=accumulator.exposure_requests,
                item_exposures=accumulator.item_exposures,
                unique_users=len(accumulator.unique_users),
                clicks=accumulator.clicks,
                saves=accumulator.saves,
                completions=accumulator.completions,
                ctr=(
                    round(accumulator.clicks / accumulator.item_exposures, 6)
                    if accumulator.item_exposures
                    else 0.0
                ),
                save_rate=(
                    round(accumulator.saves / accumulator.item_exposures, 6)
                    if accumulator.item_exposures
                    else 0.0
                ),
                completion_rate=(
                    round(accumulator.completions / accumulator.item_exposures, 6)
                    if accumulator.item_exposures
                    else 0.0
                ),
            )
            for accumulator in sorted(
                strategy_accumulators.values(),
                key=lambda item: (item.variant_key, item.strategy_name),
            )
        ]
