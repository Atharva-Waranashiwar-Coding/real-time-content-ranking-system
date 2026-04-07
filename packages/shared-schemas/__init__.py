"""Shared schemas for the real-time content ranking system."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, RootModel, field_validator


class InteractionEventType(str, Enum):
    """Types of user interactions."""

    IMPRESSION = "impression"
    CLICK = "click"
    LIKE = "like"
    SAVE = "save"
    SKIP = "skip"
    WATCH_START = "watch_start"
    WATCH_COMPLETE = "watch_complete"


class ContentCategory(str, Enum):
    """Content categories for the tech learning domain."""

    AI = "ai"
    BACKEND = "backend"
    SYSTEM_DESIGN = "system-design"
    DEVOPS = "devops"
    INTERVIEW_PREP = "interview-prep"


class ContentStatus(str, Enum):
    """Publication status for content items."""

    DRAFT = "draft"
    PUBLISHED = "published"


RANKING_TOPICS = tuple(category.value for category in ContentCategory)


def normalize_topic_preferences(
    topic_preferences: Mapping[str, float] | None,
) -> dict[str, float]:
    """Normalize and validate topic preference scores."""

    normalized_preferences: dict[str, float] = {}
    for raw_topic, raw_score in (topic_preferences or {}).items():
        topic = raw_topic.strip().lower()
        if not topic:
            raise ValueError("Topic preference keys must be non-empty")
        if topic not in RANKING_TOPICS:
            raise ValueError(
                f"Topic '{topic}' is not supported. Allowed topics: {', '.join(RANKING_TOPICS)}"
            )
        if not isinstance(raw_score, (int, float)):
            raise ValueError(f"Topic '{topic}' score must be numeric")

        score = float(raw_score)
        if score < 0 or score > 1:
            raise ValueError(f"Topic '{topic}' score must be between 0 and 1")

        normalized_preferences[topic] = score

    return normalized_preferences


class TopicPreferencesSchema(RootModel[dict[str, float]]):
    """Normalized topic preferences shared across services."""

    @field_validator("root")
    @classmethod
    def validate_root(cls, value: dict[str, float]) -> dict[str, float]:
        """Validate shared topic preferences."""

        return normalize_topic_preferences(value)


class UserProfileBaseSchema(BaseModel):
    """Shared user profile fields used across domain services."""

    bio: str | None = Field(default=None, max_length=500)
    topic_preferences: dict[str, float] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    @field_validator("bio", mode="before")
    @classmethod
    def normalize_bio(cls, value: str | None) -> str | None:
        """Normalize profile biography text."""

        if value is None:
            return None

        normalized = value.strip()
        return normalized or None

    @field_validator("topic_preferences")
    @classmethod
    def validate_topic_preferences(cls, value: dict[str, float]) -> dict[str, float]:
        """Validate topic preference scores."""

        return normalize_topic_preferences(value)


class UserSummarySchema(BaseModel):
    """Shared top-level user fields."""

    id: str
    username: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class ContentTagSchema(BaseModel):
    """Shared content tag fields."""

    id: str | None = None
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=500)

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        """Normalize tag names for consistent matching."""

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


class ContentMetadataSchema(BaseModel):
    """Shared content metadata fields."""

    title: str = Field(..., min_length=5, max_length=500)
    description: str | None = Field(default=None, max_length=2000)
    topic: str = Field(..., min_length=1, max_length=100)
    category: ContentCategory
    status: ContentStatus = ContentStatus.DRAFT

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    @field_validator("title", mode="before")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        """Normalize content titles."""

        return value.strip()

    @field_validator("description", mode="before")
    @classmethod
    def normalize_content_description(cls, value: str | None) -> str | None:
        """Normalize optional content descriptions."""

        if value is None:
            return None

        normalized = value.strip()
        return normalized or None

    @field_validator("topic", mode="before")
    @classmethod
    def normalize_topic(cls, value: str) -> str:
        """Normalize topic slugs."""

        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("Topic cannot be empty")
        return normalized


class InteractionEventSchema(BaseModel):
    """Event schema for user interactions."""

    event_id: str = Field(..., description="Unique event identifier")
    event_type: InteractionEventType
    user_id: str
    content_id: str | None = None
    session_id: str | None = None
    topic: str | None = None
    watch_duration_seconds: int = 0
    event_timestamp: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True)


class HealthCheckResponse(BaseModel):
    """Standard health check response."""

    status: str
    service: str
    version: str = "0.1.0"
    timestamp: datetime


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    message: str
    status_code: int
    timestamp: datetime


class PaginationParams(BaseModel):
    """Standard pagination parameters."""

    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    sort_by: str | None = None
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


__all__ = [
    "ContentCategory",
    "ContentMetadataSchema",
    "ContentStatus",
    "ContentTagSchema",
    "ErrorResponse",
    "HealthCheckResponse",
    "InteractionEventSchema",
    "InteractionEventType",
    "PaginationParams",
    "RANKING_TOPICS",
    "TopicPreferencesSchema",
    "UserProfileBaseSchema",
    "UserSummarySchema",
    "normalize_topic_preferences",
]
