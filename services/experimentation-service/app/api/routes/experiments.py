"""API routes for experiment assignment and exposure logging."""

from uuid import UUID

from app.core import RequestContext, get_request_context
from app.db import get_db
from app.schemas import (
    ExperimentAssignmentResponse,
    ExperimentExposureCreateRequest,
    ExperimentExposureResponse,
)
from app.services import ExperimentService, ExperimentValidationError
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/experiments", tags=["experiments"])


@router.get("/assignment", response_model=ExperimentAssignmentResponse)
async def get_assignment(
    user_id: UUID = Query(..., description="Assigned user identifier"),
    db: AsyncSession = Depends(get_db),
) -> ExperimentAssignmentResponse:
    """Return the deterministic experiment assignment for a user."""

    service = ExperimentService(db)
    return await service.get_or_create_assignment(str(user_id))


@router.post(
    "/exposures",
    response_model=ExperimentExposureResponse,
    status_code=status.HTTP_201_CREATED,
)
async def record_exposure(
    request: ExperimentExposureCreateRequest,
    request_context: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
) -> ExperimentExposureResponse:
    """Record an experiment exposure for a feed response."""

    service = ExperimentService(db)
    try:
        return await service.record_exposure(request, request_context)
    except ExperimentValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
