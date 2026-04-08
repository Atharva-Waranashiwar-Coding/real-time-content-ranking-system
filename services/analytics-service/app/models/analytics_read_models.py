"""Read models used by analytics-service for experiment comparisons."""

from app.db.base import Base
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship


class ExperimentExposure(Base):
    """Read model for experiment exposure headers."""

    __tablename__ = "experiment_exposures"

    id = Column(String(36), primary_key=True)
    schema_name = Column(String(64), nullable=False)
    experiment_key = Column(String(120), nullable=False, index=True)
    variant_key = Column(String(120), nullable=False, index=True)
    strategy_name = Column(String(120), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    session_id = Column(String(255), nullable=True, index=True)
    request_id = Column(String(64), nullable=False, index=True)
    correlation_id = Column(String(64), nullable=False, index=True)
    feed_limit = Column(Integer, nullable=False)
    feed_offset = Column(Integer, nullable=False)
    cache_hit = Column(Boolean, nullable=False, default=False)
    generated_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, index=True)
    items = relationship("ExperimentExposureItem", lazy="selectin")


class ExperimentExposureItem(Base):
    """Read model for experiment exposure items."""

    __tablename__ = "experiment_exposure_items"

    id = Column(String(36), primary_key=True)
    exposure_id = Column(
        String(36),
        ForeignKey("experiment_exposures.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content_id = Column(String(36), nullable=False, index=True)
    rank = Column(Integer, nullable=False)
    score = Column(Float, nullable=False)
    topic = Column(String(100), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False)


class Interaction(Base):
    """Read model for persisted interaction audit rows."""

    __tablename__ = "interactions"

    id = Column(String(36), primary_key=True)
    event_id = Column(String(36), nullable=False, unique=True, index=True)
    schema_name = Column(String(64), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    content_id = Column(String(36), nullable=False, index=True)
    session_id = Column(String(255), nullable=True, index=True)
    topic = Column(String(100), nullable=True, index=True)
    watch_duration_seconds = Column(Integer, nullable=False, default=0)
    kafka_topic = Column(String(100), nullable=False, index=True)
    request_id = Column(String(64), nullable=False, index=True)
    correlation_id = Column(String(64), nullable=False, index=True)
    event_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, index=True)
    published_at = Column(DateTime(timezone=True), nullable=True, index=True)
