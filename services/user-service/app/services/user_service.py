"""Business logic layer for user operations."""

from __future__ import annotations

from app.models import User, UserProfile
from app.schemas.user import (
    TopicPreferencesUpdateRequest,
    UserCreateRequest,
    UserProfileResponse,
    UserProfileUpdateRequest,
    UserResponse,
    UserUpdateRequest,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload


class UserService:
    """Service for user-related operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, request: UserCreateRequest) -> UserResponse:
        """Create a new user with an associated profile."""

        user = User(username=request.username, email=request.email)
        profile = UserProfile(
            user=user,
            bio=request.profile.bio,
            topic_preferences=dict(request.profile.topic_preferences),
        )

        try:
            self.session.add(user)
            self.session.add(profile)
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ValueError(self._build_integrity_error_message(exc, request=request)) from exc

        created_user = await self._get_user_model(user.id)
        return self._serialize_user(created_user)

    async def get_user_by_id(self, user_id: str) -> UserResponse | None:
        """Retrieve a user by ID with their profile."""

        user = await self._get_user_model(user_id)
        return self._serialize_user(user) if user else None

    async def get_user_by_username(self, username: str) -> UserResponse | None:
        """Retrieve a user by username."""

        query = (
            select(User)
            .where(User.username == username)
            .options(selectinload(User.profile))
        )
        result = await self.session.execute(query)
        user = result.scalars().first()
        return self._serialize_user(user) if user else None

    async def update_user(self, user_id: str, request: UserUpdateRequest) -> UserResponse | None:
        """Update core user information."""

        user = await self._get_user_model(user_id)
        if not user:
            return None

        if "username" in request.model_fields_set and request.username is not None:
            user.username = request.username
        if "email" in request.model_fields_set and request.email is not None:
            user.email = request.email

        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ValueError(self._build_integrity_error_message(exc, request=request)) from exc

        refreshed_user = await self._get_user_model(user_id)
        return self._serialize_user(refreshed_user)

    async def get_profile(self, user_id: str) -> UserProfileResponse | None:
        """Retrieve user profile."""

        profile = await self._get_profile_model(user_id)
        return self._serialize_profile(profile) if profile else None

    async def update_profile(
        self,
        user_id: str,
        request: UserProfileUpdateRequest,
    ) -> UserProfileResponse | None:
        """Update user profile fields."""

        profile = await self._get_profile_model(user_id)
        if not profile:
            return None

        if "bio" in request.model_fields_set:
            profile.bio = request.bio
        if "topic_preferences" in request.model_fields_set and request.topic_preferences is not None:
            profile.topic_preferences = dict(request.topic_preferences)

        await self.session.commit()
        refreshed_profile = await self._get_profile_model(user_id)
        return self._serialize_profile(refreshed_profile)

    async def update_topic_preferences(
        self,
        user_id: str,
        request: TopicPreferencesUpdateRequest,
    ) -> UserProfileResponse | None:
        """Update only topic preferences."""

        profile = await self._get_profile_model(user_id)
        if not profile:
            return None

        profile.topic_preferences = dict(request.topic_preferences)
        await self.session.commit()
        refreshed_profile = await self._get_profile_model(user_id)
        return self._serialize_profile(refreshed_profile)

    async def delete_user(self, user_id: str) -> bool:
        """Delete a user and associated profile."""

        user = await self._get_user_model(user_id)
        if not user:
            return False

        await self.session.delete(user)
        await self.session.commit()
        return True

    async def list_users(self, skip: int = 0, limit: int = 100) -> list[UserResponse]:
        """List all users with pagination."""

        query = (
            select(User)
            .options(selectinload(User.profile))
            .order_by(User.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        users = result.scalars().all()
        return [self._serialize_user(user) for user in users]

    async def _get_user_model(self, user_id: str) -> User | None:
        """Retrieve a user model with profile preloaded."""

        query = (
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.profile))
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def _get_profile_model(self, user_id: str) -> UserProfile | None:
        """Retrieve a user profile model."""

        query = select(UserProfile).where(UserProfile.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    @staticmethod
    def _serialize_user(user: User) -> UserResponse:
        """Convert ORM user models to response schemas."""

        return UserResponse.model_validate(user)

    @staticmethod
    def _serialize_profile(profile: UserProfile) -> UserProfileResponse:
        """Convert ORM profile models to response schemas."""

        return UserProfileResponse.model_validate(profile)

    @staticmethod
    def _build_integrity_error_message(
        exc: IntegrityError,
        request: UserCreateRequest | UserUpdateRequest,
    ) -> str:
        """Translate database integrity errors into explicit API messages."""

        error_text = str(exc.orig).lower()
        if "username" in error_text:
            username = getattr(request, "username", None)
            if username:
                return f"Username '{username}' already exists"
            return "Username already exists"
        if "email" in error_text:
            email = getattr(request, "email", None)
            if email:
                return f"Email '{email}' already exists"
            return "Email already exists"
        return "User request failed due to duplicate data"
