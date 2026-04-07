"""Content domain models for content-service."""

import uuid
from datetime import datetime, timezone

from app.db.base import Base
from sqlalchemy import JSON, CheckConstraint, Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship


def utc_now() -> datetime:
    """Return the current UTC timestamp."""

    return datetime.now(timezone.utc)


content_tags_association = Table(
    "content_tags_association",
    Base.metadata,
    Column("content_id", String(36), ForeignKey("content_items.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", String(36), ForeignKey("content_tags.id", ondelete="CASCADE"), primary_key=True),
)


class ContentTag(Base):
    """Content tag entity used for filtering and taxonomy."""

    __tablename__ = "content_tags"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    content_items = relationship(
        "ContentItem",
        secondary=content_tags_association,
        back_populates="tags",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<ContentTag(id={self.id}, name={self.name})>"


class ContentItem(Base):
    """Content item entity for draft and published content metadata."""

    __tablename__ = "content_items"
    __table_args__ = (
        CheckConstraint(
            "category IN ('ai', 'backend', 'system-design', 'devops', 'interview-prep')",
            name="ck_content_items_category",
        ),
        CheckConstraint(
            "status IN ('draft', 'published')",
            name="ck_content_items_status",
        ),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(500), nullable=False, index=True)
    description = Column(String(2000), nullable=True)
    topic = Column(String(100), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="draft", index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)
    published_at = Column(DateTime(timezone=True), nullable=True, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)
    view_count = Column(Integer, nullable=False, default=0)
    engagement_metadata = Column(JSON, nullable=False, default=dict)

    tags = relationship(
        "ContentTag",
        secondary=content_tags_association,
        back_populates="content_items",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<ContentItem(id={self.id}, title={self.title}, status={self.status})>"
