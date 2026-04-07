"""Content domain models for content-service."""

import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Table, Integer
from sqlalchemy.orm import relationship
from app.db.base import Base
from shared_schemas import ContentStatus


# Association table for many-to-many relationship between content items and tags
content_tags_association = Table(
    "content_tags_association",
    Base.metadata,
    Column("content_id", String(36), ForeignKey("content_items.id"), primary_key=True),
    Column("tag_id", String(36), ForeignKey("content_tags.id"), primary_key=True),
)


class ContentTag(Base):
    """Content tag entity - used for organizing and filtering content."""

    __tablename__ = "content_tags"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationship
    content_items = relationship(
        "ContentItem",
        secondary=content_tags_association,
        back_populates="tags",
    )

    def __repr__(self) -> str:
        return f"<ContentTag(id={self.id}, name={self.name})>"


class ContentItem(Base):
    """Content item entity - represents a piece of content in the system."""

    __tablename__ = "content_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(500), nullable=False, index=True)
    description = Column(String(2000), nullable=True)
    topic = Column(String(100), nullable=False, index=True)  # e.g., "ai", "backend", "system-design"
    category = Column(String(50), nullable=False, index=True)  # e.g., "ai", "backend", etc.
    status = Column(String(20), nullable=False, default="draft", index=True)  # "draft" or "published"
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    published_at = Column(DateTime(timezone=True), nullable=True, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    
    # Metadata for analytics and ranking
    view_count = Column(Integer, default=0)
    engagement_metadata = Column(JSON, nullable=False, default=dict)  # Stores engagement stats

    # Relationships
    tags = relationship(
        "ContentTag",
        secondary=content_tags_association,
        back_populates="content_items",
    )

    def __repr__(self) -> str:
        return f"<ContentItem(id={self.id}, title={self.title}, status={self.status})>"
