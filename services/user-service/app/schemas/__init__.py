"""Schemas for user-service."""

from app.schemas.user import (
    UserCreateRequest,
    UserUpdateRequest,
    UserProfileUpdateRequest,
    TopicPreferencesUpdateRequest,
    UserProfileResponse,
    UserResponse,
    UserDetailResponse,
)

__all__ = [
    "UserCreateRequest",
    "UserUpdateRequest",
    "UserProfileUpdateRequest",
    "TopicPreferencesUpdateRequest",
    "UserProfileResponse",
    "UserResponse",
    "UserDetailResponse",
]
