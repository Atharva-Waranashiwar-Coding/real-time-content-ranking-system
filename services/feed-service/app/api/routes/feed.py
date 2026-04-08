"""API routes for feed generation."""

from app.core import RequestContext, get_request_context
from app.schemas import FeedQueryParams, FeedResponse
from app.services import FeedAssemblyError, FeedService
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

router = APIRouter(prefix="/api/v1", tags=["feed"])


def get_feed_service(request: Request) -> FeedService:
    """Return the shared feed service from application state."""

    return request.app.state.feed_service


@router.get("/feed", response_model=FeedResponse)
async def get_feed(
    user_id: str = Query(..., description="User identifier"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    request_context: RequestContext = Depends(get_request_context),
    feed_service: FeedService = Depends(get_feed_service),
) -> FeedResponse:
    """Return a paginated personalized feed."""

    query_params = FeedQueryParams(user_id=user_id, limit=limit, offset=offset)
    try:
        return await feed_service.get_feed(query_params, request_context)
    except FeedAssemblyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
