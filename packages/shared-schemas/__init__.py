"""Shared schemas for the real-time content ranking system."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, RootModel, field_validator, model_validator


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


INTERACTION_EVENT_V1_SCHEMA_NAME = "interaction_event.v1"
INTERACTIONS_EVENTS_V1_TOPIC = "interactions.events.v1"
RANKING_TOPICS = tuple(category.value for category in ContentCategory)


def utc_now() -> datetime:
    """Return the current UTC timestamp."""

    return datetime.now(timezone.utc)


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


class InteractionEventV1Schema(BaseModel):
    """Versioned interaction event schema used for ingestion and publishing."""

    schema_name: str = Field(
        default=INTERACTION_EVENT_V1_SCHEMA_NAME,
        description="Explicit schema identifier for versioned event consumers",
    )
    event_id: UUID = Field(..., description="Unique event identifier")
    event_type: InteractionEventType
    user_id: UUID
    content_id: UUID
    session_id: str | None = Field(default=None, max_length=255)
    topic: str | None = Field(default=None, max_length=100)
    watch_duration_seconds: int = Field(default=0, ge=0, le=86400)
    event_timestamp: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    @field_validator("schema_name")
    @classmethod
    def validate_schema_name(cls, value: str) -> str:
        """Keep the schema identifier explicit and versioned."""

        if value != INTERACTION_EVENT_V1_SCHEMA_NAME:
            raise ValueError(
                f"schema_name must be '{INTERACTION_EVENT_V1_SCHEMA_NAME}'"
            )
        return value

    @field_validator("session_id", mode="before")
    @classmethod
    def normalize_session_id(cls, value: str | None) -> str | None:
        """Normalize optional session identifiers."""

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

    @field_validator("event_timestamp")
    @classmethod
    def ensure_timezone_aware_timestamp(cls, value: datetime) -> datetime:
        """Coerce naive timestamps to UTC for consistent event storage."""

        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @model_validator(mode="after")
    def validate_watch_event_fields(self) -> InteractionEventV1Schema:
        """Validate watch-event specific constraints."""

        if (
            self.event_type == InteractionEventType.WATCH_COMPLETE
            and self.watch_duration_seconds <= 0
        ):
            raise ValueError(
                "watch_duration_seconds must be greater than 0 for watch_complete events"
            )
        return self


class InteractionEventSchema(InteractionEventV1Schema):
    """Backward-compatible alias for the current interaction event schema."""


class InteractionAcceptedResponse(BaseModel):
    """Response returned after an interaction has been accepted for processing."""

    event_id: UUID
    schema_name: str = INTERACTION_EVENT_V1_SCHEMA_NAME
    kafka_topic: str = INTERACTIONS_EVENTS_V1_TOPIC
    status: str = "accepted"
    request_id: str
    correlation_id: str
    received_at: datetime
    published_at: datetime | None

    model_config = ConfigDict(extra="forbid")


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
    "INTERACTION_EVENT_V1_SCHEMA_NAME",
    "INTERACTIONS_EVENTS_V1_TOPIC",
    "InteractionAcceptedResponse",
    "InteractionEventV1Schema",
    "InteractionEventSchema",
    "InteractionEventType",
    "PaginationParams",
    "RANKING_TOPICS",
    "TopicPreferencesSchema",
    "UserProfileBaseSchema",
    "UserSummarySchema",
    "normalize_topic_preferences",
    "utc_now",
]
