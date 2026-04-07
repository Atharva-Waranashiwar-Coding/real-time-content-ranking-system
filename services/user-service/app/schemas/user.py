"""Pydantic schemas for user-related requests and responses."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from shared_schemas import UserProfileBaseSchema, UserSummarySchema, normalize_topic_preferences

USERNAME_PATTERN = r"^[a-zA-Z0-9][a-zA-Z0-9_-]{2,254}$"


class UserProfileCreateRequest(UserProfileBaseSchema):
    """Nested profile payload used during user creation."""


class UserCreateRequest(BaseModel):
    """Request schema for creating a user."""

    username: str = Field(
        ...,
        min_length=3,
        max_length=255,
        pattern=USERNAME_PATTERN,
        description="Unique username",
    )
    email: EmailStr = Field(..., description="Email address")
    profile: UserProfileCreateRequest = Field(
        default_factory=UserProfileCreateRequest,
        description="Initial profile payload",
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        """Normalize usernames before persistence."""

        return value.strip()

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        """Normalize email casing before persistence."""

        return value.strip().lower()


class UserUpdateRequest(BaseModel):
    """Request schema for updating a user."""

    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=255,
        pattern=USERNAME_PATTERN,
        description="Unique username",
    )
    email: EmailStr | None = Field(default=None, description="Email address")

    model_config = ConfigDict(extra="forbid")

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value: str | None) -> str | None:
        """Normalize optional usernames."""

        if value is None:
            return None
        return value.strip()

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        """Normalize optional emails."""

        if value is None:
            return None
        return value.strip().lower()

    @model_validator(mode="after")
    def validate_has_updates(self) -> UserUpdateRequest:
        """Require at least one field for updates."""

        if not self.model_fields_set:
            raise ValueError("At least one user field must be provided for update")
        return self


class UserProfileUpdateRequest(BaseModel):
    """Request schema for updating user profile."""

    bio: str | None = Field(default=None, max_length=500, description="User bio")
    topic_preferences: dict[str, float] | None = Field(
        default=None,
        description="Topic preference scores keyed by supported topic slug",
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("bio", mode="before")
    @classmethod
    def normalize_bio(cls, value: str | None) -> str | None:
        """Normalize optional profile bios."""

        if value is None:
            return None

        normalized = value.strip()
        return normalized or None

    @field_validator("topic_preferences")
    @classmethod
    def validate_topic_preferences(
        cls, value: dict[str, float] | None
    ) -> dict[str, float] | None:
        """Validate optional topic preference payloads."""

        if value is None:
            return None
        return normalize_topic_preferences(value)

    @model_validator(mode="after")
    def validate_has_updates(self) -> UserProfileUpdateRequest:
        """Require at least one profile field for updates."""

        if not self.model_fields_set:
            raise ValueError("At least one profile field must be provided for update")
        return self


class TopicPreferencesUpdateRequest(BaseModel):
    """Request schema for updating topic preferences."""

    topic_preferences: dict[str, float] = Field(..., description="Topic preference scores")

    model_config = ConfigDict(extra="forbid")

    @field_validator("topic_preferences")
    @classmethod
    def validate_topic_preferences(cls, value: dict[str, float]) -> dict[str, float]:
        """Validate required topic preference payloads."""

        normalized = normalize_topic_preferences(value)
        if not normalized:
            raise ValueError("Topic preferences cannot be empty")
        return normalized


class UserProfileResponse(UserProfileBaseSchema):
    """Response schema for user profile."""

    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserResponse(UserSummarySchema):
    """Response schema for user."""

    created_at: datetime
    updated_at: datetime
    profile: UserProfileResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class UserDetailResponse(UserResponse):
    """Extended user response with all details."""

    model_config = ConfigDict(from_attributes=True)
