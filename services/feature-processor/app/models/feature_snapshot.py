"""Snapshot models for feature-processor."""

import uuid

from app.db.base import Base
from sqlalchemy import CheckConstraint, Column, DateTime, Float, Integer, String

from shared_schemas import (
    CONTENT_FEATURES_V1_SCHEMA_NAME,
    USER_TOPIC_AFFINITY_V1_SCHEMA_NAME,
    utc_now,
)


class ContentFeatureSnapshot(Base):
    """Periodic snapshot of the materialized content feature vector."""

    __tablename__ = "content_feature_snapshots"
    __table_args__ = (
        CheckConstraint(
            f"schema_name = '{CONTENT_FEATURES_V1_SCHEMA_NAME}'",
            name="ck_content_feature_snapshots_schema_name",
        ),
        CheckConstraint(
            "window_hours > 0",
            name="ck_content_feature_snapshots_window_hours_positive",
        ),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    schema_name = Column(String(64), nullable=False, index=True)
    content_id = Column(String(36), nullable=False, index=True)
    topic = Column(String(100), nullable=True, index=True)
    window_hours = Column(Integer, nullable=False)
    impressions = Column(Integer, nullable=False, default=0)
    clicks = Column(Integer, nullable=False, default=0)
    likes = Column(Integer, nullable=False, default=0)
    saves = Column(Integer, nullable=False, default=0)
    skip_count = Column(Integer, nullable=False, default=0)
    watch_starts = Column(Integer, nullable=False, default=0)
    watch_completes = Column(Integer, nullable=False, default=0)
    ctr = Column(Float, nullable=False, default=0.0)
    like_rate = Column(Float, nullable=False, default=0.0)
    save_rate = Column(Float, nullable=False, default=0.0)
    skip_rate = Column(Float, nullable=False, default=0.0)
    completion_rate = Column(Float, nullable=False, default=0.0)
    trending_score = Column(Float, nullable=False, default=0.0)
    last_event_at = Column(DateTime(timezone=True), nullable=True)
    snapshot_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)

    def __repr__(self) -> str:
        return (
            f"<ContentFeatureSnapshot(content_id={self.content_id}, "
            f"trending_score={self.trending_score})>"
        )


class UserTopicFeatureSnapshot(Base):
    """Periodic snapshot of per-user topic affinity signals."""

    __tablename__ = "user_topic_feature_snapshots"
    __table_args__ = (
        CheckConstraint(
            f"schema_name = '{USER_TOPIC_AFFINITY_V1_SCHEMA_NAME}'",
            name="ck_user_topic_feature_snapshots_schema_name",
        ),
        CheckConstraint(
            "window_hours > 0",
            name="ck_user_topic_feature_snapshots_window_hours_positive",
        ),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    schema_name = Column(String(64), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    topic = Column(String(100), nullable=False, index=True)
    window_hours = Column(Integer, nullable=False)
    impressions = Column(Integer, nullable=False, default=0)
    clicks = Column(Integer, nullable=False, default=0)
    likes = Column(Integer, nullable=False, default=0)
    saves = Column(Integer, nullable=False, default=0)
    skip_count = Column(Integer, nullable=False, default=0)
    watch_starts = Column(Integer, nullable=False, default=0)
    watch_completes = Column(Integer, nullable=False, default=0)
    affinity_score = Column(Float, nullable=False, default=0.0)
    last_event_at = Column(DateTime(timezone=True), nullable=True)
    snapshot_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)

    def __repr__(self) -> str:
        return (
            f"<UserTopicFeatureSnapshot(user_id={self.user_id}, topic={self.topic}, "
            f"affinity_score={self.affinity_score})>"
        )
