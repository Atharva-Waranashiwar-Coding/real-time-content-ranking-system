"""API routes for interaction ingestion."""

from app.core import RequestContext, get_request_context
from app.db import get_db
from app.schemas import InteractionCreateRequest, InteractionIngestResponse
from app.services import (
    DuplicateInteractionEventError,
    InteractionPublishError,
    InteractionService,
)
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from shared_clients import KafkaProducer

router = APIRouter(prefix="/api/v1/interactions", tags=["interactions"])


def get_event_producer(request: Request) -> KafkaProducer:
    """Dependency returning the configured Kafka producer."""

    producer = getattr(request.app.state, "kafka_producer", None)
    if producer is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Kafka producer is not initialized",
        )
    return producer


@router.post("", response_model=InteractionIngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_interaction(
    interaction: InteractionCreateRequest,
    request_context: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
    event_producer: KafkaProducer = Depends(get_event_producer),
) -> InteractionIngestResponse:
    """Persist and publish a validated interaction event."""

    service = InteractionService(db, event_producer)

    try:
        return await service.ingest_interaction(interaction, request_context)
    except DuplicateInteractionEventError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except InteractionPublishError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
