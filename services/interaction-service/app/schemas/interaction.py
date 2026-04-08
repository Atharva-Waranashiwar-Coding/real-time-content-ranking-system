"""Schemas for interaction ingestion."""

from pydantic import ConfigDict

from shared_schemas import InteractionAcceptedResponse, InteractionEventV1Schema


class InteractionCreateRequest(InteractionEventV1Schema):
    """Interaction ingestion request backed by the shared v1 event schema."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)


class InteractionIngestResponse(InteractionAcceptedResponse):
    """Response returned when an interaction event has been accepted."""

    model_config = ConfigDict(extra="forbid")
