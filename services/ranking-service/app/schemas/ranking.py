"""Schemas for ranking-service requests and responses."""

from pydantic import ConfigDict

from shared_schemas import RankingRequestV1Schema, RankingResponseV1Schema


class RankingRequest(RankingRequestV1Schema):
    """Internal ranking request schema."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)


class RankingResponse(RankingResponseV1Schema):
    """Internal ranking response schema."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)
