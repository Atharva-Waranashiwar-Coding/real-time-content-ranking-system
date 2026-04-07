"""Shared schemas for the real-time content ranking system."""

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class InteractionEventType(str, Enum):
    """Types of user interactions."""

    IMPRESSION = "impression"
    CLICK = "click"
    LIKE = "like"
    SAVE = "save"
    SKIP = "skip"
    WATCH_START = "watch_start"
    WATCH_COMPLETE = "watch_complete"


class InteractionEventSchema(BaseModel):
    """Event schema for user interactions."""

    event_id: str = Field(..., description="Unique event identifier")
    event_type: InteractionEventType
    user_id: str
    content_id: Optional[str] = None
    session_id: Optional[str] = None
    topic: Optional[str] = None
    watch_duration_seconds: int = 0
    event_timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class HealthCheckResponse(BaseModel):
    """Standard health check response."""

    status: str
    service: str
    version: str = "0.1.0"
    timestamp: datetime


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    message: str
    status_code: int
    timestamp: datetime


class PaginationParams(BaseModel):
    """Standard pagination parameters."""

    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    sort_by: Optional[str] = None
    sort_order: str = Field(default="desc", regex="^(asc|desc)$")


__all__ = [
    "InteractionEventType",
    "InteractionEventSchema",
    "HealthCheckResponse",
    "ErrorResponse",
    "PaginationParams",
]
