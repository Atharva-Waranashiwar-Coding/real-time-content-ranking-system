"""Schemas for user-service."""

from app.schemas.user import (
    TopicPreferencesUpdateRequest,
    UserCreateRequest,
    UserDetailResponse,
    UserProfileCreateRequest,
    UserProfileResponse,
    UserProfileUpdateRequest,
    UserResponse,
    UserUpdateRequest,
)

__all__ = [
    "UserCreateRequest",
    "UserUpdateRequest",
    "UserProfileCreateRequest",
    "UserProfileUpdateRequest",
    "TopicPreferencesUpdateRequest",
    "UserProfileResponse",
    "UserResponse",
    "UserDetailResponse",
]
