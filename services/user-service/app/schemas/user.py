"""Pydantic schemas for user-related requests and responses."""

from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel, Field, EmailStr, validator


class UserCreateRequest(BaseModel):
    """Request schema for creating a user."""

    username: str = Field(..., min_length=3, max_length=255, description="Username")
    email: EmailStr = Field(..., description="Email address")


class UserUpdateRequest(BaseModel):
    """Request schema for updating a user."""

    email: Optional[EmailStr] = Field(None, description="Email address")


class UserProfileUpdateRequest(BaseModel):
    """Request schema for updating user profile."""

    bio: Optional[str] = Field(None, max_length=500, description="User bio")
    topic_preferences: Optional[Dict[str, float]] = Field(None, description="Topic preference scores (0-1)")

    @validator("topic_preferences")
    def validate_topic_preferences(cls, v):
        """Validate topic preference values are between 0 and 1."""
        if v:
            for topic, score in v.items():
                if not isinstance(score, (int, float)) or score < 0 or score > 1:
                    raise ValueError(f"Topic '{topic}' score must be between 0 and 1, got {score}")
        return v


class TopicPreferencesUpdateRequest(BaseModel):
    """Request schema for updating topic preferences."""

    topic_preferences: Dict[str, float] = Field(..., description="Topic preference scores")

    @validator("topic_preferences")
    def validate_topic_preferences(cls, v):
        """Validate topic preference values are between 0 and 1."""
        if not v:
            raise ValueError("Topic preferences cannot be empty")
        for topic, score in v.items():
            if not isinstance(score, (int, float)) or score < 0 or score > 1:
                raise ValueError(f"Topic '{topic}' score must be between 0 and 1")
        return v


class UserProfileResponse(BaseModel):
    """Response schema for user profile."""

    id: str
    user_id: str
    bio: Optional[str]
    topic_preferences: Dict[str, float]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """Response schema for user."""

    id: str
    username: str
    email: str
    created_at: datetime
    updated_at: datetime
    profile: Optional[UserProfileResponse]

    class Config:
        from_attributes = True


class UserDetailResponse(UserResponse):
    """Extended user response with all details."""

    pass
