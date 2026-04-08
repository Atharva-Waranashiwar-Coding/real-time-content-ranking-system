"""Shared schemas for the real-time content ranking system."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from enum import Enum
from math import isfinite
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


class CandidateSource(str, Enum):
    """Candidate retrieval source identifiers used by feed generation."""

    RECENT = "recent"
    TRENDING = "trending"
    TOPIC_AFFINITY = "topic_affinity"


INTERACTION_EVENT_V1_SCHEMA_NAME = "interaction_event.v1"
INTERACTIONS_EVENTS_V1_TOPIC = "interactions.events.v1"
CONTENT_FEATURES_V1_SCHEMA_NAME = "content_features.v1"
USER_TOPIC_AFFINITY_V1_SCHEMA_NAME = "user_topic_affinity.v1"
RANKING_REQUEST_V1_SCHEMA_NAME = "ranking_request.v1"
RANKING_RESPONSE_V1_SCHEMA_NAME = "ranking_response.v1"
RANKING_DECISION_V1_SCHEMA_NAME = "ranking_decision.v1"
RANKING_DECISIONS_V1_TOPIC = "ranking.decisions.v1"
FEED_RESPONSE_V1_SCHEMA_NAME = "feed_response.v1"
EXPERIMENT_ASSIGNMENT_V1_SCHEMA_NAME = "experiment_assignment.v1"
EXPERIMENT_EXPOSURE_CREATE_V1_SCHEMA_NAME = "experiment_exposure_create.v1"
EXPERIMENT_EXPOSURE_V1_SCHEMA_NAME = "experiment_exposure.v1"
EXPERIMENT_COMPARISON_V1_SCHEMA_NAME = "experiment_comparison.v1"
HOME_FEED_RANKING_EXPERIMENT_KEY = "home_feed_ranking.v1"
RULES_V1_RANKING_STRATEGY = "rules_v1"
RULES_V2_TRENDING_BOOST_RANKING_STRATEGY = "rules_v2_with_trending_boost"
SUPPORTED_RANKING_STRATEGIES = (
    RULES_V1_RANKING_STRATEGY,
    RULES_V2_TRENDING_BOOST_RANKING_STRATEGY,
)
RULES_BASED_RANKING_STRATEGY = RULES_V1_RANKING_STRATEGY
DEFAULT_FEATURE_WINDOW_HOURS = 24
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


class ContentFeaturesV1Schema(BaseModel):
    """Versioned content feature vector used by downstream ranking consumers."""

    schema_name: str = Field(
        default=CONTENT_FEATURES_V1_SCHEMA_NAME,
        description="Explicit schema identifier for content feature consumers",
    )
    content_id: UUID
    topic: str | None = Field(default=None, max_length=100)
    window_hours: int = Field(default=DEFAULT_FEATURE_WINDOW_HOURS, ge=1, le=720)
    impressions: int = Field(default=0, ge=0)
    clicks: int = Field(default=0, ge=0)
    likes: int = Field(default=0, ge=0)
    saves: int = Field(default=0, ge=0)
    skip_count: int = Field(default=0, ge=0)
    watch_starts: int = Field(default=0, ge=0)
    watch_completes: int = Field(default=0, ge=0)
    ctr: float = Field(default=0.0, ge=0.0, le=1.0)
    like_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    save_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    skip_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    completion_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    trending_score: float = 0.0
    last_event_at: datetime | None = None
    updated_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(extra="forbid")

    @field_validator("schema_name")
    @classmethod
    def validate_schema_name(cls, value: str) -> str:
        """Keep the content feature schema identifier explicit and versioned."""

        if value != CONTENT_FEATURES_V1_SCHEMA_NAME:
            raise ValueError(
                f"schema_name must be '{CONTENT_FEATURES_V1_SCHEMA_NAME}'"
            )
        return value

    @field_validator("topic", mode="before")
    @classmethod
    def normalize_topic(cls, value: str | None) -> str | None:
        """Normalize optional topic slugs."""

        if value is None:
            return None

        normalized = value.strip().lower()
        return normalized or None

    @field_validator("last_event_at", "updated_at")
    @classmethod
    def ensure_timezone_aware_timestamp(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        """Coerce naive timestamps to UTC for consistent feature storage."""

        if value is None:
            return None
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class UserTopicAffinityV1Schema(BaseModel):
    """Versioned user topic affinity vector for ranking consumers."""

    schema_name: str = Field(
        default=USER_TOPIC_AFFINITY_V1_SCHEMA_NAME,
        description="Explicit schema identifier for user affinity consumers",
    )
    user_id: UUID
    window_hours: int = Field(default=DEFAULT_FEATURE_WINDOW_HOURS, ge=1, le=720)
    topic_affinity: dict[str, float] = Field(default_factory=dict)
    last_event_at: datetime | None = None
    updated_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(extra="forbid")

    @field_validator("schema_name")
    @classmethod
    def validate_schema_name(cls, value: str) -> str:
        """Keep the user affinity schema identifier explicit and versioned."""

        if value != USER_TOPIC_AFFINITY_V1_SCHEMA_NAME:
            raise ValueError(
                f"schema_name must be '{USER_TOPIC_AFFINITY_V1_SCHEMA_NAME}'"
            )
        return value

    @field_validator("topic_affinity")
    @classmethod
    def validate_topic_affinity(
        cls,
        value: dict[str, float],
    ) -> dict[str, float]:
        """Validate shared user affinity scores across supported topics."""

        normalized_affinity: dict[str, float] = {}
        for raw_topic, raw_score in value.items():
            topic = raw_topic.strip().lower()
            if not topic:
                raise ValueError("Topic affinity keys must be non-empty")
            if topic not in RANKING_TOPICS:
                raise ValueError(
                    f"Topic '{topic}' is not supported. Allowed topics: {', '.join(RANKING_TOPICS)}"
                )
            if not isinstance(raw_score, (int, float)):
                raise ValueError(f"Topic '{topic}' score must be numeric")

            score = float(raw_score)
            if not isfinite(score):
                raise ValueError(f"Topic '{topic}' score must be finite")

            normalized_affinity[topic] = score

        return normalized_affinity

    @field_validator("last_event_at", "updated_at")
    @classmethod
    def ensure_timezone_aware_timestamp(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        """Coerce naive timestamps to UTC for consistent feature storage."""

        if value is None:
            return None
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class RankingScoreBreakdownV1Schema(BaseModel):
    """Explainable score breakdown for a ranked content item."""

    user_topic_affinity: float = Field(default=0.0, ge=0.0, le=1.0)
    user_topic_affinity_weighted: float = 0.0
    recency: float = Field(default=0.0, ge=0.0, le=1.0)
    recency_weighted: float = 0.0
    engagement: float = Field(default=0.0, ge=0.0, le=1.0)
    engagement_weighted: float = 0.0
    trending: float = Field(default=0.0, ge=0.0, le=1.0)
    trending_weighted: float = 0.0
    strategy_adjustment: float = 0.0
    diversity_penalty: float = Field(default=0.0, ge=0.0)
    final_score: float = 0.0

    model_config = ConfigDict(extra="forbid")


class RankingCandidateV1Schema(BaseModel):
    """Candidate item submitted to ranking-service for scoring."""

    content_id: UUID
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=2000)
    topic: str = Field(..., min_length=1, max_length=100)
    category: ContentCategory
    published_at: datetime | None = None
    candidate_sources: list[CandidateSource] = Field(default_factory=list)
    user_topic_affinity: float = Field(default=0.0, ge=0.0, le=1.0)
    content_features: ContentFeaturesV1Schema

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    @field_validator("title", mode="before")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        """Normalize ranking candidate titles."""

        return value.strip()

    @field_validator("description", mode="before")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        """Normalize optional ranking candidate descriptions."""

        if value is None:
            return None

        normalized = value.strip()
        return normalized or None

    @field_validator("topic", mode="before")
    @classmethod
    def normalize_topic(cls, value: str) -> str:
        """Normalize candidate topics for scoring consistency."""

        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("Topic cannot be empty")
        return normalized

    @field_validator("candidate_sources")
    @classmethod
    def normalize_candidate_sources(
        cls,
        value: list[CandidateSource],
    ) -> list[CandidateSource]:
        """De-duplicate candidate sources while preserving order."""

        deduplicated_sources: list[CandidateSource] = []
        for source in value:
            if source not in deduplicated_sources:
                deduplicated_sources.append(source)
        return deduplicated_sources

    @field_validator("published_at")
    @classmethod
    def ensure_timezone_aware_published_at(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        """Coerce candidate publication timestamps to UTC."""

        if value is None:
            return None
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @model_validator(mode="after")
    def validate_feature_alignment(self) -> RankingCandidateV1Schema:
        """Ensure the embedded feature vector matches the candidate item."""

        if self.content_features.content_id != self.content_id:
            raise ValueError("content_features.content_id must match content_id")
        return self


class RankedContentItemV1Schema(RankingCandidateV1Schema):
    """Ranked content item returned by ranking-service and feed-service."""

    rank: int = Field(..., ge=1)
    score: float
    score_breakdown: RankingScoreBreakdownV1Schema

    model_config = ConfigDict(extra="forbid", use_enum_values=True)


class RankingRequestV1Schema(BaseModel):
    """Versioned request payload sent to ranking-service."""

    schema_name: str = Field(
        default=RANKING_REQUEST_V1_SCHEMA_NAME,
        description="Explicit schema identifier for ranking requests",
    )
    strategy_name: str = Field(
        default=RULES_BASED_RANKING_STRATEGY,
        min_length=1,
        max_length=100,
    )
    user_id: UUID
    candidates: list[RankingCandidateV1Schema] = Field(default_factory=list)
    apply_diversity_penalty: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    @field_validator("schema_name")
    @classmethod
    def validate_schema_name(cls, value: str) -> str:
        """Keep the ranking request schema identifier explicit and versioned."""

        if value != RANKING_REQUEST_V1_SCHEMA_NAME:
            raise ValueError(
                f"schema_name must be '{RANKING_REQUEST_V1_SCHEMA_NAME}'"
            )
        return value

    @field_validator("strategy_name", mode="before")
    @classmethod
    def validate_strategy_name(cls, value: str) -> str:
        """Validate the requested strategy identifier."""

        normalized = value.strip()
        if normalized == "rules_based.v1":
            return RULES_V1_RANKING_STRATEGY
        if normalized not in SUPPORTED_RANKING_STRATEGIES:
            raise ValueError(
                "strategy_name must be one of "
                f"{', '.join(SUPPORTED_RANKING_STRATEGIES)}"
            )
        return normalized


class RankingResponseV1Schema(BaseModel):
    """Versioned response payload returned by ranking-service."""

    schema_name: str = Field(
        default=RANKING_RESPONSE_V1_SCHEMA_NAME,
        description="Explicit schema identifier for ranking responses",
    )
    decision_id: UUID
    strategy_name: str = RULES_BASED_RANKING_STRATEGY
    user_id: UUID
    candidate_count: int = Field(default=0, ge=0)
    ranked_items: list[RankedContentItemV1Schema] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    @field_validator("schema_name")
    @classmethod
    def validate_schema_name(cls, value: str) -> str:
        """Keep the ranking response schema identifier explicit and versioned."""

        if value != RANKING_RESPONSE_V1_SCHEMA_NAME:
            raise ValueError(
                f"schema_name must be '{RANKING_RESPONSE_V1_SCHEMA_NAME}'"
            )
        return value

    @field_validator("strategy_name", mode="before")
    @classmethod
    def validate_strategy_name(cls, value: str) -> str:
        """Validate ranking response strategy identifiers."""

        normalized = value.strip()
        if normalized == "rules_based.v1":
            return RULES_V1_RANKING_STRATEGY
        if normalized not in SUPPORTED_RANKING_STRATEGIES:
            raise ValueError(
                "strategy_name must be one of "
                f"{', '.join(SUPPORTED_RANKING_STRATEGIES)}"
            )
        return normalized

    @field_validator("generated_at")
    @classmethod
    def ensure_timezone_aware_generated_at(cls, value: datetime) -> datetime:
        """Coerce response timestamps to UTC."""

        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class RankingDecisionEventV1Schema(BaseModel):
    """Versioned ranking decision event emitted by ranking-service."""

    schema_name: str = Field(
        default=RANKING_DECISION_V1_SCHEMA_NAME,
        description="Explicit schema identifier for ranking decision events",
    )
    decision_id: UUID
    strategy_name: str = RULES_BASED_RANKING_STRATEGY
    user_id: UUID
    candidate_count: int = Field(default=0, ge=0)
    ranked_items: list[RankedContentItemV1Schema] = Field(default_factory=list)
    request_id: str
    correlation_id: str
    generated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    @field_validator("schema_name")
    @classmethod
    def validate_schema_name(cls, value: str) -> str:
        """Keep the ranking decision schema identifier explicit and versioned."""

        if value != RANKING_DECISION_V1_SCHEMA_NAME:
            raise ValueError(
                f"schema_name must be '{RANKING_DECISION_V1_SCHEMA_NAME}'"
            )
        return value

    @field_validator("strategy_name", mode="before")
    @classmethod
    def validate_strategy_name(cls, value: str) -> str:
        """Validate ranking decision strategy identifiers."""

        normalized = value.strip()
        if normalized == "rules_based.v1":
            return RULES_V1_RANKING_STRATEGY
        if normalized not in SUPPORTED_RANKING_STRATEGIES:
            raise ValueError(
                "strategy_name must be one of "
                f"{', '.join(SUPPORTED_RANKING_STRATEGIES)}"
            )
        return normalized

    @field_validator("request_id", "correlation_id", mode="before")
    @classmethod
    def normalize_request_identifiers(cls, value: str) -> str:
        """Normalize trace identifiers included in ranking decision events."""

        normalized = value.strip()
        if not normalized:
            raise ValueError("request_id and correlation_id cannot be empty")
        return normalized

    @field_validator("generated_at")
    @classmethod
    def ensure_timezone_aware_generated_at(cls, value: datetime) -> datetime:
        """Coerce decision timestamps to UTC."""

        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class ExperimentAssignmentV1Schema(BaseModel):
    """Versioned deterministic experiment assignment returned by experimentation-service."""

    schema_name: str = Field(
        default=EXPERIMENT_ASSIGNMENT_V1_SCHEMA_NAME,
        description="Explicit schema identifier for experiment assignments",
    )
    experiment_key: str = Field(..., min_length=1, max_length=120)
    variant_key: str = Field(..., min_length=1, max_length=120)
    strategy_name: str = Field(..., min_length=1, max_length=120)
    user_id: UUID
    assignment_bucket: int = Field(..., ge=0, le=9999)
    assigned_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(extra="forbid")

    @field_validator("schema_name")
    @classmethod
    def validate_schema_name(cls, value: str) -> str:
        """Keep the assignment schema identifier explicit and versioned."""

        if value != EXPERIMENT_ASSIGNMENT_V1_SCHEMA_NAME:
            raise ValueError(
                f"schema_name must be '{EXPERIMENT_ASSIGNMENT_V1_SCHEMA_NAME}'"
            )
        return value

    @field_validator("experiment_key", "variant_key", mode="before")
    @classmethod
    def normalize_identifiers(cls, value: str) -> str:
        """Normalize experiment and variant identifiers."""

        normalized = value.strip()
        if not normalized:
            raise ValueError("experiment_key and variant_key cannot be empty")
        return normalized

    @field_validator("strategy_name", mode="before")
    @classmethod
    def validate_strategy_name(cls, value: str) -> str:
        """Validate and normalize assigned ranking strategies."""

        normalized = value.strip()
        if normalized == "rules_based.v1":
            return RULES_V1_RANKING_STRATEGY
        if normalized not in SUPPORTED_RANKING_STRATEGIES:
            raise ValueError(
                "strategy_name must be one of "
                f"{', '.join(SUPPORTED_RANKING_STRATEGIES)}"
            )
        return normalized

    @field_validator("assigned_at")
    @classmethod
    def ensure_timezone_aware_assigned_at(cls, value: datetime) -> datetime:
        """Coerce assignment timestamps to UTC."""

        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class ExperimentExposureItemV1Schema(BaseModel):
    """Item-level experiment exposure payload recorded for a feed response."""

    content_id: UUID
    rank: int = Field(..., ge=1)
    score: float
    topic: str = Field(..., min_length=1, max_length=100)
    category: ContentCategory

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    @field_validator("topic", mode="before")
    @classmethod
    def normalize_topic(cls, value: str) -> str:
        """Normalize exposed topic identifiers."""

        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("topic cannot be empty")
        return normalized


class ExperimentExposureCreateV1Schema(BaseModel):
    """Request payload used by feed-service to record experiment exposures."""

    schema_name: str = Field(
        default=EXPERIMENT_EXPOSURE_CREATE_V1_SCHEMA_NAME,
        description="Explicit schema identifier for experiment exposure writes",
    )
    experiment_key: str = Field(..., min_length=1, max_length=120)
    variant_key: str = Field(..., min_length=1, max_length=120)
    strategy_name: str = Field(..., min_length=1, max_length=120)
    user_id: UUID
    session_id: str | None = Field(default=None, max_length=255)
    feed_limit: int = Field(default=20, ge=1, le=100)
    feed_offset: int = Field(default=0, ge=0)
    cache_hit: bool = False
    generated_at: datetime = Field(default_factory=utc_now)
    items: list[ExperimentExposureItemV1Schema] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    @field_validator("schema_name")
    @classmethod
    def validate_schema_name(cls, value: str) -> str:
        """Keep the exposure write schema identifier explicit and versioned."""

        if value != EXPERIMENT_EXPOSURE_CREATE_V1_SCHEMA_NAME:
            raise ValueError(
                f"schema_name must be '{EXPERIMENT_EXPOSURE_CREATE_V1_SCHEMA_NAME}'"
            )
        return value

    @field_validator("experiment_key", "variant_key", mode="before")
    @classmethod
    def normalize_identifiers(cls, value: str) -> str:
        """Normalize experiment exposure identifiers."""

        normalized = value.strip()
        if not normalized:
            raise ValueError("experiment_key and variant_key cannot be empty")
        return normalized

    @field_validator("strategy_name", mode="before")
    @classmethod
    def validate_strategy_name(cls, value: str) -> str:
        """Validate and normalize exposure strategy names."""

        normalized = value.strip()
        if normalized == "rules_based.v1":
            return RULES_V1_RANKING_STRATEGY
        if normalized not in SUPPORTED_RANKING_STRATEGIES:
            raise ValueError(
                "strategy_name must be one of "
                f"{', '.join(SUPPORTED_RANKING_STRATEGIES)}"
            )
        return normalized

    @field_validator("session_id", mode="before")
    @classmethod
    def normalize_session_id(cls, value: str | None) -> str | None:
        """Normalize optional session identifiers."""

        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("generated_at")
    @classmethod
    def ensure_timezone_aware_generated_at(cls, value: datetime) -> datetime:
        """Coerce exposure timestamps to UTC."""

        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class ExperimentExposureV1Schema(BaseModel):
    """Versioned persisted experiment exposure response."""

    schema_name: str = Field(
        default=EXPERIMENT_EXPOSURE_V1_SCHEMA_NAME,
        description="Explicit schema identifier for experiment exposure responses",
    )
    exposure_id: UUID
    experiment_key: str = Field(..., min_length=1, max_length=120)
    variant_key: str = Field(..., min_length=1, max_length=120)
    strategy_name: str = Field(..., min_length=1, max_length=120)
    user_id: UUID
    recorded_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(extra="forbid")

    @field_validator("schema_name")
    @classmethod
    def validate_schema_name(cls, value: str) -> str:
        """Keep the exposure response schema identifier explicit and versioned."""

        if value != EXPERIMENT_EXPOSURE_V1_SCHEMA_NAME:
            raise ValueError(
                f"schema_name must be '{EXPERIMENT_EXPOSURE_V1_SCHEMA_NAME}'"
            )
        return value

    @field_validator("experiment_key", "variant_key", mode="before")
    @classmethod
    def normalize_identifiers(cls, value: str) -> str:
        """Normalize experiment exposure identifiers."""

        normalized = value.strip()
        if not normalized:
            raise ValueError("experiment_key and variant_key cannot be empty")
        return normalized

    @field_validator("strategy_name", mode="before")
    @classmethod
    def validate_strategy_name(cls, value: str) -> str:
        """Validate and normalize exposure strategy names."""

        normalized = value.strip()
        if normalized == "rules_based.v1":
            return RULES_V1_RANKING_STRATEGY
        if normalized not in SUPPORTED_RANKING_STRATEGIES:
            raise ValueError(
                "strategy_name must be one of "
                f"{', '.join(SUPPORTED_RANKING_STRATEGIES)}"
            )
        return normalized

    @field_validator("recorded_at")
    @classmethod
    def ensure_timezone_aware_recorded_at(cls, value: datetime) -> datetime:
        """Coerce exposure timestamps to UTC."""

        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class StrategyOutcomeMetricsV1Schema(BaseModel):
    """Aggregated strategy outcome metrics for experiment comparisons."""

    variant_key: str = Field(..., min_length=1, max_length=120)
    strategy_name: str = Field(..., min_length=1, max_length=120)
    exposure_requests: int = Field(default=0, ge=0)
    item_exposures: int = Field(default=0, ge=0)
    unique_users: int = Field(default=0, ge=0)
    clicks: int = Field(default=0, ge=0)
    saves: int = Field(default=0, ge=0)
    completions: int = Field(default=0, ge=0)
    ctr: float = Field(default=0.0, ge=0.0, le=1.0)
    save_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    completion_rate: float = Field(default=0.0, ge=0.0, le=1.0)

    model_config = ConfigDict(extra="forbid")

    @field_validator("variant_key", mode="before")
    @classmethod
    def normalize_variant_key(cls, value: str) -> str:
        """Normalize experiment variant identifiers."""

        normalized = value.strip()
        if not normalized:
            raise ValueError("variant_key cannot be empty")
        return normalized

    @field_validator("strategy_name", mode="before")
    @classmethod
    def validate_strategy_name(cls, value: str) -> str:
        """Validate and normalize aggregated strategy names."""

        normalized = value.strip()
        if normalized == "rules_based.v1":
            return RULES_V1_RANKING_STRATEGY
        if normalized not in SUPPORTED_RANKING_STRATEGIES:
            raise ValueError(
                "strategy_name must be one of "
                f"{', '.join(SUPPORTED_RANKING_STRATEGIES)}"
            )
        return normalized


class ExperimentComparisonV1Schema(BaseModel):
    """Aggregated comparison payload for an experiment across strategies."""

    schema_name: str = Field(
        default=EXPERIMENT_COMPARISON_V1_SCHEMA_NAME,
        description="Explicit schema identifier for experiment comparison responses",
    )
    experiment_key: str = Field(..., min_length=1, max_length=120)
    lookback_hours: int = Field(default=168, ge=1, le=8760)
    strategies: list[StrategyOutcomeMetricsV1Schema] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(extra="forbid")

    @field_validator("schema_name")
    @classmethod
    def validate_schema_name(cls, value: str) -> str:
        """Keep the comparison schema identifier explicit and versioned."""

        if value != EXPERIMENT_COMPARISON_V1_SCHEMA_NAME:
            raise ValueError(
                f"schema_name must be '{EXPERIMENT_COMPARISON_V1_SCHEMA_NAME}'"
            )
        return value

    @field_validator("experiment_key", mode="before")
    @classmethod
    def normalize_experiment_key(cls, value: str) -> str:
        """Normalize experiment identifiers used by analytics responses."""

        normalized = value.strip()
        if not normalized:
            raise ValueError("experiment_key cannot be empty")
        return normalized

    @field_validator("generated_at")
    @classmethod
    def ensure_timezone_aware_generated_at(cls, value: datetime) -> datetime:
        """Coerce comparison timestamps to UTC."""

        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class FeedResponseV1Schema(BaseModel):
    """Versioned feed response returned by feed-service."""

    schema_name: str = Field(
        default=FEED_RESPONSE_V1_SCHEMA_NAME,
        description="Explicit schema identifier for feed responses",
    )
    user_id: UUID
    items: list[RankedContentItemV1Schema] = Field(default_factory=list)
    total_candidates: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    has_more: bool = False
    cache_hit: bool = False
    experiment_assignment: ExperimentAssignmentV1Schema | None = None
    exposure_id: UUID | None = None
    generated_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    @field_validator("schema_name")
    @classmethod
    def validate_schema_name(cls, value: str) -> str:
        """Keep the feed response schema identifier explicit and versioned."""

        if value != FEED_RESPONSE_V1_SCHEMA_NAME:
            raise ValueError(
                f"schema_name must be '{FEED_RESPONSE_V1_SCHEMA_NAME}'"
            )
        return value

    @field_validator("generated_at")
    @classmethod
    def ensure_timezone_aware_generated_at(cls, value: datetime) -> datetime:
        """Coerce feed timestamps to UTC."""

        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


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
    "CandidateSource",
    "ContentCategory",
    "ContentFeaturesV1Schema",
    "ContentMetadataSchema",
    "ContentStatus",
    "ContentTagSchema",
    "CONTENT_FEATURES_V1_SCHEMA_NAME",
    "DEFAULT_FEATURE_WINDOW_HOURS",
    "ErrorResponse",
    "EXPERIMENT_ASSIGNMENT_V1_SCHEMA_NAME",
    "EXPERIMENT_COMPARISON_V1_SCHEMA_NAME",
    "EXPERIMENT_EXPOSURE_CREATE_V1_SCHEMA_NAME",
    "EXPERIMENT_EXPOSURE_V1_SCHEMA_NAME",
    "FEED_RESPONSE_V1_SCHEMA_NAME",
    "ExperimentAssignmentV1Schema",
    "ExperimentComparisonV1Schema",
    "ExperimentExposureCreateV1Schema",
    "ExperimentExposureItemV1Schema",
    "ExperimentExposureV1Schema",
    "FeedResponseV1Schema",
    "HealthCheckResponse",
    "HOME_FEED_RANKING_EXPERIMENT_KEY",
    "INTERACTION_EVENT_V1_SCHEMA_NAME",
    "INTERACTIONS_EVENTS_V1_TOPIC",
    "InteractionAcceptedResponse",
    "InteractionEventV1Schema",
    "InteractionEventSchema",
    "InteractionEventType",
    "PaginationParams",
    "RANKING_DECISION_V1_SCHEMA_NAME",
    "RANKING_DECISIONS_V1_TOPIC",
    "RANKING_REQUEST_V1_SCHEMA_NAME",
    "RANKING_RESPONSE_V1_SCHEMA_NAME",
    "RANKING_TOPICS",
    "RULES_BASED_RANKING_STRATEGY",
    "RULES_V1_RANKING_STRATEGY",
    "RULES_V2_TRENDING_BOOST_RANKING_STRATEGY",
    "RankedContentItemV1Schema",
    "RankingCandidateV1Schema",
    "RankingDecisionEventV1Schema",
    "RankingRequestV1Schema",
    "RankingResponseV1Schema",
    "RankingScoreBreakdownV1Schema",
    "SUPPORTED_RANKING_STRATEGIES",
    "StrategyOutcomeMetricsV1Schema",
    "TopicPreferencesSchema",
    "USER_TOPIC_AFFINITY_V1_SCHEMA_NAME",
    "UserTopicAffinityV1Schema",
    "UserProfileBaseSchema",
    "UserSummarySchema",
    "normalize_topic_preferences",
    "utc_now",
]
