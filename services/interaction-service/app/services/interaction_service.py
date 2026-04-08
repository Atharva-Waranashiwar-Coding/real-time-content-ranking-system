"""Business logic for interaction ingestion."""

from __future__ import annotations

import logging
from time import perf_counter

from app.core.config import config
from app.core.request_context import RequestContext
from app.models import Interaction
from app.schemas import InteractionCreateRequest, InteractionIngestResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from shared_clients import KafkaMessage, KafkaProducer, KafkaProducerError
from shared_logging import observe_event_operation
from shared_schemas import INTERACTIONS_EVENTS_V1_TOPIC, utc_now

logger = logging.getLogger(config.SERVICE_NAME)


class DuplicateInteractionEventError(ValueError):
    """Raised when an interaction event ID has already been ingested."""


class InteractionPublishError(RuntimeError):
    """Raised when Kafka publication fails after audit persistence."""


class InteractionService:
    """Service for validating, persisting, and publishing interaction events."""

    def __init__(self, session: AsyncSession, event_producer: KafkaProducer):
        self.session = session
        self.event_producer = event_producer

    async def ingest_interaction(
        self,
        event: InteractionCreateRequest,
        request_context: RequestContext,
    ) -> InteractionIngestResponse:
        """Persist an interaction event and publish it to Kafka."""

        publish_started_at = perf_counter()
        persisted_interaction = Interaction(
            event_id=str(event.event_id),
            schema_name=event.schema_name,
            event_type=event.event_type,
            user_id=str(event.user_id),
            content_id=str(event.content_id),
            session_id=event.session_id,
            topic=event.topic,
            watch_duration_seconds=event.watch_duration_seconds,
            event_metadata=dict(event.metadata),
            event_payload=event.model_dump(mode="json"),
            kafka_topic=config.KAFKA_INTERACTIONS_TOPIC,
            request_id=request_context.request_id,
            correlation_id=request_context.correlation_id,
            event_timestamp=event.event_timestamp,
        )

        self.session.add(persisted_interaction)

        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            if "event_id" in str(exc.orig).lower():
                logger.warning(
                    "Duplicate interaction event rejected",
                    extra={
                        **request_context.to_log_fields(),
                        "event_id": str(event.event_id),
                        "schema_name": event.schema_name,
                    },
                )
                raise DuplicateInteractionEventError(
                    f"Interaction event '{event.event_id}' already exists"
                ) from exc
            raise

        await self.session.refresh(persisted_interaction)

        logger.info(
            "Interaction event persisted",
            extra={
                **request_context.to_log_fields(),
                "event_id": persisted_interaction.event_id,
                "event_type": persisted_interaction.event_type,
                "schema_name": persisted_interaction.schema_name,
                "kafka_topic": persisted_interaction.kafka_topic,
            },
        )

        kafka_message = KafkaMessage(
            topic=INTERACTIONS_EVENTS_V1_TOPIC,
            key=str(event.user_id),
            value=event.model_dump(mode="json"),
            headers={
                "schema-name": event.schema_name,
                "event-id": str(event.event_id),
                "event-type": event.event_type,
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
                topic=INTERACTIONS_EVENTS_V1_TOPIC,
                outcome="failure",
                duration_seconds=perf_counter() - publish_started_at,
            )
            logger.error(
                "Kafka publish failed for interaction event",
                extra={
                    **request_context.to_log_fields(),
                    "event_id": persisted_interaction.event_id,
                    "event_type": persisted_interaction.event_type,
                    "schema_name": persisted_interaction.schema_name,
                    "kafka_topic": persisted_interaction.kafka_topic,
                },
            )
            raise InteractionPublishError(
                "Interaction persisted but Kafka publish failed; retry is required"
            ) from exc

        observe_event_operation(
            service_name=config.SERVICE_NAME,
            operation="publish",
            topic=INTERACTIONS_EVENTS_V1_TOPIC,
            outcome="success",
            duration_seconds=perf_counter() - publish_started_at,
        )

        persisted_interaction.published_at = utc_now()
        await self.session.commit()
        await self.session.refresh(persisted_interaction)

        logger.info(
            "Interaction event published",
            extra={
                **request_context.to_log_fields(),
                "event_id": persisted_interaction.event_id,
                "event_type": persisted_interaction.event_type,
                "schema_name": persisted_interaction.schema_name,
                "kafka_topic": persisted_interaction.kafka_topic,
                "published_at": persisted_interaction.published_at.isoformat(),
            },
        )

        return InteractionIngestResponse(
            event_id=event.event_id,
            schema_name=event.schema_name,
            kafka_topic=persisted_interaction.kafka_topic,
            request_id=request_context.request_id,
            correlation_id=request_context.correlation_id,
            received_at=persisted_interaction.created_at,
            published_at=persisted_interaction.published_at,
        )

    async def get_interaction_by_event_id(self, event_id: str) -> Interaction | None:
        """Retrieve a persisted interaction by event ID."""

        result = await self.session.execute(
            select(Interaction).where(Interaction.event_id == event_id)
        )
        return result.scalars().first()
