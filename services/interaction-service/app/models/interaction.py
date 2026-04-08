"""Interaction audit models for interaction-service."""

import uuid

from app.db.base import Base
from sqlalchemy import JSON, CheckConstraint, Column, DateTime, Integer, String

from shared_schemas import INTERACTION_EVENT_V1_SCHEMA_NAME, utc_now


class Interaction(Base):
    """Immutable interaction event persisted for audit and replay."""

    __tablename__ = "interactions"
    __table_args__ = (
        CheckConstraint(
            (
                "event_type IN ("
                "'impression', 'click', 'like', 'save', 'skip', 'watch_start', 'watch_complete'"
                ")"
            ),
            name="ck_interactions_event_type",
        ),
        CheckConstraint(
            f"schema_name = '{INTERACTION_EVENT_V1_SCHEMA_NAME}'",
            name="ck_interactions_schema_name",
        ),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(36), nullable=False, unique=True, index=True)
    schema_name = Column(String(64), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    content_id = Column(String(36), nullable=False, index=True)
    session_id = Column(String(255), nullable=True, index=True)
    topic = Column(String(100), nullable=True, index=True)
    watch_duration_seconds = Column(Integer, nullable=False, default=0)
    event_metadata = Column("metadata", JSON, nullable=False, default=dict)
    event_payload = Column(JSON, nullable=False)
    kafka_topic = Column(String(100), nullable=False, index=True)
    request_id = Column(String(64), nullable=False, index=True)
    correlation_id = Column(String(64), nullable=False, index=True)
    event_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)
    published_at = Column(DateTime(timezone=True), nullable=True, index=True)

    def __repr__(self) -> str:
        return (
            f"<Interaction(event_id={self.event_id}, event_type={self.event_type}, "
            f"user_id={self.user_id}, content_id={self.content_id})>"
        )
