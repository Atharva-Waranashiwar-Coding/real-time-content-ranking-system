"""Business logic layer for user operations."""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from app.models import User, UserProfile
from app.schemas.user import (
    UserCreateRequest,
    UserUpdateRequest,
    UserProfileUpdateRequest,
    UserResponse,
    UserProfileResponse,
)


class UserService:
    """Service for user-related operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, request: UserCreateRequest) -> UserResponse:
        """Create a new user with an associated profile."""
        try:
            # Create user
            user = User(username=request.username, email=request.email)
            self.session.add(user)
            await self.session.flush()

            # Create associated profile
            profile = UserProfile(user_id=user.id, topic_preferences={})
            self.session.add(profile)

            await self.session.commit()
            await self.session.refresh(user, ["profile"])
            return UserResponse.from_orm(user)
        except IntegrityError as e:
            await self.session.rollback()
            if "username" in str(e.orig):
                raise ValueError(f"Username '{request.username}' already exists")
            elif "email" in str(e.orig):
                raise ValueError(f"Email '{request.email}' already exists")
            raise ValueError("User creation failed due to duplicate data")

    async def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        """Retrieve a user by ID with their profile."""
        query = select(User).where(User.id == user_id)
        result = await self.session.execute(query)
        user = result.scalars().first()
        return UserResponse.from_orm(user) if user else None

    async def get_user_by_username(self, username: str) -> Optional[UserResponse]:
        """Retrieve a user by username."""
        query = select(User).where(User.username == username)
        result = await self.session.execute(query)
        user = result.scalars().first()
        return UserResponse.from_orm(user) if user else None

    async def update_user(self, user_id: str, request: UserUpdateRequest) -> Optional[UserResponse]:
        """Update user information."""
        query = select(User).where(User.id == user_id)
        result = await self.session.execute(query)
        user = result.scalars().first()

        if not user:
            return None

        try:
            if request.email:
                user.email = request.email
            await self.session.commit()
            await self.session.refresh(user, ["profile"])
            return UserResponse.from_orm(user)
        except IntegrityError as e:
            await self.session.rollback()
            if "email" in str(e.orig):
                raise ValueError(f"Email '{request.email}' already exists")
            raise ValueError("User update failed")

    async def get_profile(self, user_id: str) -> Optional[UserProfileResponse]:
        """Retrieve user profile."""
        query = select(UserProfile).where(UserProfile.user_id == user_id)
        result = await self.session.execute(query)
        profile = result.scalars().first()
        return UserProfileResponse.from_orm(profile) if profile else None

    async def update_profile(self, user_id: str, request: UserProfileUpdateRequest) -> Optional[UserProfileResponse]:
        """Update user profile."""
        query = select(UserProfile).where(UserProfile.user_id == user_id)
        result = await self.session.execute(query)
        profile = result.scalars().first()

        if not profile:
            return None

        if request.bio is not None:
            profile.bio = request.bio
        if request.topic_preferences is not None:
            profile.topic_preferences = request.topic_preferences

        await self.session.commit()
        await self.session.refresh(profile)
        return UserProfileResponse.from_orm(profile)

    async def update_topic_preferences(self, user_id: str, topic_preferences: dict) -> Optional[UserProfileResponse]:
        """Update only topic preferences."""
        query = select(UserProfile).where(UserProfile.user_id == user_id)
        result = await self.session.execute(query)
        profile = result.scalars().first()

        if not profile:
            return None

        profile.topic_preferences = topic_preferences
        await self.session.commit()
        await self.session.refresh(profile)
        return UserProfileResponse.from_orm(profile)

    async def delete_user(self, user_id: str) -> bool:
        """Delete a user and associated profile."""
        query = select(User).where(User.id == user_id)
        result = await self.session.execute(query)
        user = result.scalars().first()

        if not user:
            return False

        await self.session.delete(user)
        await self.session.commit()
        return True

    async def list_users(self, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        """List all users with pagination."""
        query = select(User).offset(skip).limit(limit)
        result = await self.session.execute(query)
        users = result.scalars().all()
        return [UserResponse.from_orm(u) for u in users]
