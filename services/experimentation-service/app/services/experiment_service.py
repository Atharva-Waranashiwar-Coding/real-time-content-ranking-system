"""Business logic for deterministic assignments and exposure persistence."""

from __future__ import annotations

import hashlib
import logging

from app.core import RequestContext, config
from app.models import ExperimentAssignment, ExperimentExposure, ExperimentExposureItem
from app.schemas import (
    ExperimentAssignmentResponse,
    ExperimentExposureCreateRequest,
    ExperimentExposureResponse,
)
from app.services.definitions import (
    ExperimentDefinition,
    ExperimentVariantDefinition,
    get_active_experiment,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select

from shared_schemas import (
    EXPERIMENT_ASSIGNMENT_V1_SCHEMA_NAME,
    EXPERIMENT_EXPOSURE_V1_SCHEMA_NAME,
    utc_now,
)

logger = logging.getLogger(config.SERVICE_NAME)


class ExperimentValidationError(ValueError):
    """Raised when an exposure payload does not match the stored assignment."""


class ExperimentService:
    """Service for deterministic assignments and feed exposure persistence."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_assignment(self, user_id: str) -> ExperimentAssignmentResponse:
        """Return the deterministic assignment for the active experiment."""

        experiment = get_active_experiment()
        existing_assignment = await self._get_assignment(experiment.experiment_key, user_id)
        if existing_assignment is not None:
            return self._build_assignment_response(existing_assignment)

        assignment_bucket = self._compute_assignment_bucket(experiment.experiment_key, user_id)
        variant = self._resolve_variant(experiment, assignment_bucket)
        assignment = ExperimentAssignment(
            schema_name=EXPERIMENT_ASSIGNMENT_V1_SCHEMA_NAME,
            experiment_key=experiment.experiment_key,
            variant_key=variant.variant_key,
            strategy_name=variant.strategy_name,
            user_id=user_id,
            assignment_bucket=assignment_bucket,
        )

        self.session.add(assignment)
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            assignment = await self._get_assignment(experiment.experiment_key, user_id)
            if assignment is None:
                raise
            return self._build_assignment_response(assignment)

        await self.session.refresh(assignment)
        logger.info(
            "Experiment assignment created",
            extra={
                "experiment_key": assignment.experiment_key,
                "variant_key": assignment.variant_key,
                "strategy_name": assignment.strategy_name,
                "user_id": assignment.user_id,
                "assignment_bucket": assignment.assignment_bucket,
            },
        )
        return self._build_assignment_response(assignment)

    async def record_exposure(
        self,
        request: ExperimentExposureCreateRequest,
        request_context: RequestContext,
    ) -> ExperimentExposureResponse:
        """Persist an experiment exposure and its item-level rows."""

        assignment = await self._get_assignment(request.experiment_key, str(request.user_id))
        if assignment is None:
            raise ExperimentValidationError(
                "Experiment assignment must exist before exposures can be recorded"
            )
        if assignment.variant_key != request.variant_key:
            raise ExperimentValidationError("Exposure variant does not match stored assignment")
        if assignment.strategy_name != request.strategy_name:
            raise ExperimentValidationError("Exposure strategy does not match stored assignment")

        exposure = ExperimentExposure(
            schema_name=EXPERIMENT_EXPOSURE_V1_SCHEMA_NAME,
            experiment_key=request.experiment_key,
            variant_key=request.variant_key,
            strategy_name=request.strategy_name,
            user_id=str(request.user_id),
            session_id=request.session_id,
            request_id=request_context.request_id,
            correlation_id=request_context.correlation_id,
            feed_limit=request.feed_limit,
            feed_offset=request.feed_offset,
            cache_hit=request.cache_hit,
            generated_at=request.generated_at,
            created_at=utc_now(),
            items=[
                ExperimentExposureItem(
                    content_id=str(item.content_id),
                    rank=item.rank,
                    score=item.score,
                    topic=item.topic,
                    category=item.category,
                )
                for item in request.items
            ],
        )

        self.session.add(exposure)
        await self.session.commit()
        await self.session.refresh(exposure)

        logger.info(
            "Experiment exposure recorded",
            extra={
                **request_context.to_log_fields(),
                "exposure_id": exposure.id,
                "experiment_key": exposure.experiment_key,
                "variant_key": exposure.variant_key,
                "strategy_name": exposure.strategy_name,
                "user_id": exposure.user_id,
                "item_count": len(request.items),
                "cache_hit": exposure.cache_hit,
            },
        )

        return ExperimentExposureResponse(
            exposure_id=exposure.id,
            experiment_key=exposure.experiment_key,
            variant_key=exposure.variant_key,
            strategy_name=exposure.strategy_name,
            user_id=exposure.user_id,
            recorded_at=exposure.created_at,
        )

    async def _get_assignment(
        self,
        experiment_key: str,
        user_id: str,
    ) -> ExperimentAssignment | None:
        """Return the persisted assignment for a user and experiment."""

        query = select(ExperimentAssignment).where(
            ExperimentAssignment.experiment_key == experiment_key,
            ExperimentAssignment.user_id == user_id,
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    @staticmethod
    def _compute_assignment_bucket(experiment_key: str, user_id: str) -> int:
        """Compute a stable 0..9999 assignment bucket for the user."""

        hash_bytes = hashlib.sha256(f"{experiment_key}:{user_id}".encode()).digest()
        return int.from_bytes(hash_bytes[:8], byteorder="big") % 10000

    @staticmethod
    def _resolve_variant(
        experiment: ExperimentDefinition,
        assignment_bucket: int,
    ) -> ExperimentVariantDefinition:
        """Resolve the configured variant for the provided bucket."""

        cumulative_allocation = 0
        for variant in experiment.variants:
            cumulative_allocation += variant.allocation_basis_points
            if assignment_bucket < cumulative_allocation:
                return variant
        return experiment.variants[-1]

    @staticmethod
    def _build_assignment_response(
        assignment: ExperimentAssignment,
    ) -> ExperimentAssignmentResponse:
        """Convert a persisted assignment model into the API response schema."""

        return ExperimentAssignmentResponse(
            experiment_key=assignment.experiment_key,
            variant_key=assignment.variant_key,
            strategy_name=assignment.strategy_name,
            user_id=assignment.user_id,
            assignment_bucket=assignment.assignment_bucket,
            assigned_at=assignment.assigned_at,
        )
