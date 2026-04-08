"""API routes for experiment comparison analytics."""

from app.core import RequestContext, config, get_request_context
from app.db import get_db
from app.schemas import ExperimentComparisonResponse
from app.services import AnalyticsService
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/experiments", tags=["experiments"])


@router.get("/{experiment_key}/comparison", response_model=ExperimentComparisonResponse)
async def get_experiment_comparison(
    experiment_key: str,
    lookback_hours: int = Query(
        config.DEFAULT_EXPERIMENT_LOOKBACK_HOURS,
        ge=1,
        le=8760,
        description="Hours of exposure history to include in the comparison window",
    ),
    request_context: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
) -> ExperimentComparisonResponse:
    """Return aggregated experiment metrics by ranking strategy."""

    service = AnalyticsService(db)
    return await service.get_experiment_comparison(
        experiment_key=experiment_key,
        lookback_hours=lookback_hours,
        request_context=request_context,
    )
