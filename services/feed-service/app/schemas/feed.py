"""Schemas for feed-service requests, upstream payloads, and responses."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from shared_schemas import (
    ContentMetadataSchema,
    ContentTagSchema,
    FeedResponseV1Schema,
    UserProfileBaseSchema,
    UserSummarySchema,
)


class FeedQueryParams(BaseModel):
    """Query parameters accepted by the feed endpoint."""

    user_id: UUID
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

    model_config = ConfigDict(extra="forbid")


class UpstreamUserProfile(UserProfileBaseSchema):
    """Subset of user profile fields needed for candidate retrieval."""

    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(extra="forbid")


class UpstreamUserResponse(UserSummarySchema):
    """User payload returned by user-service."""

    created_at: datetime
    updated_at: datetime
    profile: UpstreamUserProfile | None = None

    model_config = ConfigDict(extra="forbid")


class UpstreamContentTag(ContentTagSchema):
    """Tag payload returned by content-service."""

    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(extra="forbid")


class UpstreamContentItem(ContentMetadataSchema):
    """Content payload returned by content-service."""

    id: str
    view_count: int
    engagement_metadata: dict[str, Any]
    created_at: datetime
    published_at: datetime | None
    updated_at: datetime
    tags: list[UpstreamContentTag] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @field_validator("published_at", "created_at", "updated_at")
    @classmethod
    def ensure_timezone_aware_timestamps(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        """Keep upstream timestamps timezone-aware."""

        if value is None:
            return None
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class UpstreamContentListResponse(BaseModel):
    """List payload returned by content-service."""

    items: list[UpstreamContentItem]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(extra="forbid")


class FeedResponse(FeedResponseV1Schema):
    """Feed response returned by feed-service."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)
