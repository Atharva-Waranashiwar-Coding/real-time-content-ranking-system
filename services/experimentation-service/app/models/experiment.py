"""Experiment assignment and exposure models."""

import uuid

from app.db.base import Base
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from shared_schemas import (
    EXPERIMENT_ASSIGNMENT_V1_SCHEMA_NAME,
    EXPERIMENT_EXPOSURE_V1_SCHEMA_NAME,
    utc_now,
)


class ExperimentAssignment(Base):
    """Deterministic ranking experiment assignment for a user."""

    __tablename__ = "experiment_assignments"
    __table_args__ = (
        UniqueConstraint(
            "experiment_key",
            "user_id",
            name="uq_experiment_assignments_experiment_user",
        ),
        CheckConstraint(
            f"schema_name = '{EXPERIMENT_ASSIGNMENT_V1_SCHEMA_NAME}'",
            name="ck_experiment_assignments_schema_name",
        ),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    schema_name = Column(String(64), nullable=False)
    experiment_key = Column(String(120), nullable=False, index=True)
    variant_key = Column(String(120), nullable=False, index=True)
    strategy_name = Column(String(120), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    assignment_bucket = Column(Integer, nullable=False)
    assigned_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class ExperimentExposure(Base):
    """Persisted feed exposure for a ranking experiment."""

    __tablename__ = "experiment_exposures"
    __table_args__ = (
        CheckConstraint(
            f"schema_name = '{EXPERIMENT_EXPOSURE_V1_SCHEMA_NAME}'",
            name="ck_experiment_exposures_schema_name",
        ),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
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
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)
    items = relationship(
        "ExperimentExposureItem",
        back_populates="exposure",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ExperimentExposureItem(Base):
    """Item-level exposure rows used for analytics attribution."""

    __tablename__ = "experiment_exposure_items"
    __table_args__ = (
        UniqueConstraint(
            "exposure_id",
            "content_id",
            name="uq_experiment_exposure_items_exposure_content",
        ),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
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
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    exposure = relationship("ExperimentExposure", back_populates="items")
