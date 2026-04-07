"""User domain models for user-service."""

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base


class User(Base):
    """User entity - core user account."""

    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationship
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"


class UserProfile(Base):
    """User profile entity - extended user information and preferences."""

    __tablename__ = "user_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    bio = Column(String(500), nullable=True)
    topic_preferences = Column(JSON, nullable=False, default=dict)  # e.g., {"ai": 0.8, "backend": 0.6, ...}
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationship
    user = relationship("User", back_populates="profile")

    def __repr__(self) -> str:
        return f"<UserProfile(user_id={self.user_id}, bio_len={len(self.bio) if self.bio else 0})>"
