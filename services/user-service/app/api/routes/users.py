"""API routes for user endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.services import UserService
from app.schemas.user import (
    UserCreateRequest,
    UserUpdateRequest,
    UserProfileUpdateRequest,
    TopicPreferencesUpdateRequest,
    UserResponse,
    UserProfileResponse,
)

router = APIRouter(prefix="/api/v1/users", tags=["users"])


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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Retrieve a user by ID."""
    service = UserService(db)
    user = await service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found",
        )
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID '{user_id}' not found",
            )
        return updated_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{user_id}/profile", response_model=UserProfileResponse)
async def get_profile(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> UserProfileResponse:
    """Retrieve user profile."""
    service = UserService(db)
    profile = await service.get_profile(user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile for user '{user_id}' not found",
        )
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile for user '{user_id}' not found",
            )
        return updated_profile
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put("/{user_id}/topics", response_model=UserProfileResponse)
async def update_topics(
    user_id: str,
    request: TopicPreferencesUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> UserProfileResponse:
    """Update user topic preferences."""
    service = UserService(db)
    try:
        updated_profile = await service.update_topic_preferences(user_id, request.topic_preferences)
        if not updated_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile for user '{user_id}' not found",
            )
        return updated_profile
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("", response_model=list[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> list[UserResponse]:
    """List all users with pagination."""
    service = UserService(db)
    return await service.list_users(skip=skip, limit=limit)
