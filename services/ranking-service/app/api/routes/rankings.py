"""API routes for ranking-service scoring endpoints."""

from app.core import RequestContext, get_request_context
from app.schemas import RankingRequest, RankingResponse
from app.services import RankingDecisionPublishError, RankingService
from fastapi import APIRouter, Depends, HTTPException, Request, status

from shared_clients import KafkaProducer

router = APIRouter(prefix="/api/v1", tags=["rankings"])


def get_event_producer(request: Request) -> KafkaProducer:
    """Return the shared Kafka producer from application state."""

    return request.app.state.kafka_producer


@router.post("/rankings", response_model=RankingResponse)
async def rank_content(
    ranking_request: RankingRequest,
    request_context: RequestContext = Depends(get_request_context),
    event_producer: KafkaProducer = Depends(get_event_producer),
) -> RankingResponse:
    """Score and order candidate content items."""

    service = RankingService(event_producer)
    try:
        return await service.rank_candidates(ranking_request, request_context)
    except RankingDecisionPublishError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
