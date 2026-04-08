"""Schemas for feature-processor health and operational state."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProcessorHealthResponse(BaseModel):
    """Health and readiness response for feature-processor."""

    status: str
    service: str
    version: str = "0.1.0"
    timestamp: datetime
    consumer_running: bool
    redis_available: bool
    database_available: bool
    last_processed_at: datetime | None = None
    last_snapshot_at: datetime | None = None
    processed_events_total: int = 0
    failed_events_total: int = 0
    dirty_content_feature_count: int = 0
    dirty_user_topic_feature_count: int = 0

    model_config = ConfigDict(extra="forbid")
