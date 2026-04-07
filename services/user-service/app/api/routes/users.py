"""API routes for user endpoints."""

from app.db import get_db
from app.schemas.user import (
    TopicPreferencesUpdateRequest,
    UserCreateRequest,
    UserProfileResponse,
    UserProfileUpdateRequest,
    UserResponse,
    UserUpdateRequest,
)
from app.services import UserService
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/users", tags=["users"])


def _raise_bad_request(detail: str) -> None:
    """Raise a standard 400 API error."""

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def _raise_not_found(resource_name: str, resource_id: str) -> None:
    """Raise a standard 404 API error."""

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{resource_name} '{resource_id}' not found",
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: UserCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Create a new user."""
    service = UserService(db)
    try:
        return await service.create_user(request)
    except ValueError as e:
        _raise_bad_request(str(e))


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Retrieve a user by ID."""
    service = UserService(db)
    user = await service.get_user_by_id(user_id)
    if not user:
        _raise_not_found("User", user_id)
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    request: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Update a user."""
    service = UserService(db)
    try:
        updated_user = await service.update_user(user_id, request)
        if not updated_user:
            _raise_not_found("User", user_id)
        return updated_user
    except ValueError as e:
        _raise_bad_request(str(e))


@router.get("/{user_id}/profile", response_model=UserProfileResponse)
async def get_profile(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> UserProfileResponse:
    """Retrieve user profile."""
    service = UserService(db)
    profile = await service.get_profile(user_id)
    if not profile:
        _raise_not_found("Profile for user", user_id)
    return profile


@router.put("/{user_id}/profile", response_model=UserProfileResponse)
async def update_profile(
    user_id: str,
    request: UserProfileUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> UserProfileResponse:
    """Update user profile."""
    service = UserService(db)
    try:
        updated_profile = await service.update_profile(user_id, request)
        if not updated_profile:
            _raise_not_found("Profile for user", user_id)
        return updated_profile
    except ValueError as e:
        _raise_bad_request(str(e))


@router.put("/{user_id}/topics", response_model=UserProfileResponse)
async def update_topics(
    user_id: str,
    request: TopicPreferencesUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> UserProfileResponse:
    """Update user topic preferences."""
    service = UserService(db)
    try:
        updated_profile = await service.update_topic_preferences(user_id, request)
        if not updated_profile:
            _raise_not_found("Profile for user", user_id)
        return updated_profile
    except ValueError as e:
        _raise_bad_request(str(e))


@router.get("", response_model=list[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
) -> list[UserResponse]:
    """List all users with pagination."""
    service = UserService(db)
    return await service.list_users(skip=skip, limit=limit)
