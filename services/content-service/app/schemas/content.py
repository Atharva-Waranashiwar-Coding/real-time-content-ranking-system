"""Pydantic schemas for content-related requests and responses."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from shared_schemas import ContentCategory, ContentMetadataSchema, ContentStatus, ContentTagSchema


class ContentTagRequest(BaseModel):
    """Request schema for creating a content tag."""

    name: str = Field(..., min_length=1, max_length=255, description="Tag name")
    description: str | None = Field(default=None, max_length=500, description="Tag description")

    model_config = ConfigDict(extra="forbid")

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        """Normalize tag names before persistence."""

        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("Tag name cannot be empty")
        return normalized

    @field_validator("description", mode="before")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        """Normalize optional tag descriptions."""

        if value is None:
            return None

        normalized = value.strip()
        return normalized or None


class ContentTagResponse(ContentTagSchema):
    """Response schema for a tag."""

    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ContentItemCreateRequest(ContentMetadataSchema):
    """Request schema for creating a content item."""

    tag_ids: list[str] = Field(default_factory=list, description="List of tag IDs to attach")

    model_config = ConfigDict(extra="forbid")

    @field_validator("tag_ids")
    @classmethod
    def validate_tag_ids(cls, value: list[str]) -> list[str]:
        """Validate tag ID payloads."""

        return [tag_id.strip() for tag_id in value if tag_id.strip()]


class ContentItemUpdateRequest(BaseModel):
    """Request schema for updating a content item."""

    title: str | None = Field(default=None, min_length=5, max_length=500, description="Content title")
    description: str | None = Field(default=None, max_length=2000, description="Content description")
    topic: str | None = Field(default=None, min_length=1, max_length=100, description="Topic slug")
    category: ContentCategory | None = Field(default=None, description="Content category")
    status: ContentStatus | None = Field(default=None, description="Content status")
    tag_ids: list[str] | None = Field(default=None, description="List of tag IDs to attach")

    model_config = ConfigDict(extra="forbid")

    @field_validator("title", mode="before")
    @classmethod
    def normalize_title(cls, value: str | None) -> str | None:
        """Normalize optional titles."""

        if value is None:
            return None
        return value.strip()

    @field_validator("description", mode="before")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        """Normalize optional descriptions."""

        if value is None:
            return None

        normalized = value.strip()
        return normalized or None

    @field_validator("topic", mode="before")
    @classmethod
    def normalize_topic(cls, value: str | None) -> str | None:
        """Normalize optional topic slugs."""

        if value is None:
            return None

        normalized = value.strip().lower()
        return normalized or None

    @field_validator("tag_ids")
    @classmethod
    def validate_tag_ids(cls, value: list[str] | None) -> list[str] | None:
        """Normalize optional tag IDs."""

        if value is None:
            return None
        return [tag_id.strip() for tag_id in value if tag_id.strip()]

    @model_validator(mode="after")
    def validate_has_updates(self) -> ContentItemUpdateRequest:
        """Require at least one field for updates."""

        if not self.model_fields_set:
            raise ValueError("At least one content field must be provided for update")
        return self


class ContentItemResponse(ContentMetadataSchema):
    """Response schema for a content item."""

    id: str
    view_count: int
    engagement_metadata: dict[str, Any]
    created_at: datetime
    published_at: datetime | None
    updated_at: datetime
    tags: list[ContentTagResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ContentItemListResponse(BaseModel):
    """Response schema for listing content items."""

    items: list[ContentItemResponse]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(extra="forbid")
