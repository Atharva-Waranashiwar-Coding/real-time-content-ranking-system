"""Business logic for ranking-service."""

from __future__ import annotations

import logging
from time import perf_counter
from uuid import uuid4

from app.core import RequestContext, config
from app.schemas import RankingRequest, RankingResponse
from app.services.scoring import rank_candidates

from shared_clients import KafkaMessage, KafkaProducer, KafkaProducerError
from shared_logging import observe_event_operation, observe_ranking_duration
from shared_schemas import (
    RANKING_DECISIONS_V1_TOPIC,
    RankingDecisionEventV1Schema,
    utc_now,
)

logger = logging.getLogger(config.SERVICE_NAME)


class RankingDecisionPublishError(RuntimeError):
    """Raised when ranking decision publication to Kafka fails."""


class RankingService:
    """Service that scores candidates and publishes ranking decision events."""

    def __init__(self, event_producer: KafkaProducer):
        self.event_producer = event_producer

    async def rank_candidates(
        self,
        request: RankingRequest,
        request_context: RequestContext,
    ) -> RankingResponse:
        """Rank candidate items and publish the resulting decision event."""

        started_at = perf_counter()
        generated_at = utc_now()
        decision_id = uuid4()
        ranked_items = rank_candidates(
            request.candidates,
            strategy_name=request.strategy_name,
            apply_diversity_penalty=request.apply_diversity_penalty,
            now=generated_at,
        )
        ranking_response = RankingResponse(
            decision_id=decision_id,
            strategy_name=request.strategy_name,
            user_id=request.user_id,
            candidate_count=len(request.candidates),
            ranked_items=ranked_items,
            generated_at=generated_at,
        )

        decision_event = RankingDecisionEventV1Schema(
            decision_id=decision_id,
            strategy_name=request.strategy_name,
            user_id=request.user_id,
            candidate_count=len(request.candidates),
            ranked_items=ranked_items,
            request_id=request_context.request_id,
            correlation_id=request_context.correlation_id,
            generated_at=generated_at,
            metadata=dict(request.metadata),
        )

        kafka_message = KafkaMessage(
            topic=RANKING_DECISIONS_V1_TOPIC,
            key=str(request.user_id),
            value=decision_event.model_dump(mode="json"),
            headers={
                "schema-name": decision_event.schema_name,
                "decision-id": str(decision_id),
                "request-id": request_context.request_id,
                "correlation-id": request_context.correlation_id,
            },
        )

        try:
            await self.event_producer.publish(kafka_message)
        except KafkaProducerError as exc:
            observe_event_operation(
                service_name=config.SERVICE_NAME,
                operation="publish",
                topic=RANKING_DECISIONS_V1_TOPIC,
                outcome="failure",
                duration_seconds=perf_counter() - started_at,
            )
            logger.error(
                "Kafka publish failed for ranking decision event",
                extra={
                    **request_context.to_log_fields(),
                    "decision_id": str(decision_id),
                    "schema_name": decision_event.schema_name,
                    "kafka_topic": RANKING_DECISIONS_V1_TOPIC,
                },
            )
            raise RankingDecisionPublishError(
                "Ranking completed but decision event publication failed"
            ) from exc

        total_duration_seconds = perf_counter() - started_at
        observe_ranking_duration(
            service_name=config.SERVICE_NAME,
            strategy_name=request.strategy_name,
            duration_seconds=total_duration_seconds,
        )
        observe_event_operation(
            service_name=config.SERVICE_NAME,
            operation="publish",
            topic=RANKING_DECISIONS_V1_TOPIC,
            outcome="success",
            duration_seconds=total_duration_seconds,
        )

        logger.info(
            "Ranking decision published",
            extra={
                **request_context.to_log_fields(),
                "decision_id": str(decision_id),
                "candidate_count": len(request.candidates),
                "returned_count": len(ranked_items),
                "strategy_name": request.strategy_name,
                "kafka_topic": RANKING_DECISIONS_V1_TOPIC,
            },
        )

        return ranking_response
