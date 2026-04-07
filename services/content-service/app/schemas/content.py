"""Pydantic schemas for content-related requests and responses."""

from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, validator
from shared_schemas import ContentCategory, ContentStatus


class ContentTagRequest(BaseModel):
    """Request schema for creating/updating a tag."""

    name: str = Field(..., min_length=1, max_length=255, description="Tag name")
    description: Optional[str] = Field(None, max_length=500, description="Tag description")


class ContentTagResponse(BaseModel):
    """Response schema for a tag."""

    id: str
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContentItemCreateRequest(BaseModel):
    """Request schema for creating a content item."""

    title: str = Field(..., min_length=5, max_length=500, description="Content title")
    description: Optional[str] = Field(None, max_length=2000, description="Content description")
    topic: str = Field(..., min_length=1, max_length=100, description="Topic (e.g., 'ai', 'backend')")
    category: ContentCategory = Field(..., description="Content category")
    tag_ids: Optional[List[str]] = Field(None, description="List of tag IDs to attach")


class ContentItemUpdateRequest(BaseModel):
    """Request schema for updating a content item."""

    title: Optional[str] = Field(None, min_length=5, max_length=500, description="Content title")
    description: Optional[str] = Field(None, max_length=2000, description="Content description")
    topic: Optional[str] = Field(None, min_length=1, max_length=100, description="Topic")
    category: Optional[ContentCategory] = Field(None, description="Content category")
    tag_ids: Optional[List[str]] = Field(None, description="List of tag IDs to attach")


class ContentItemPublishRequest(BaseModel):
    """Request schema for publishing a content item."""

    pass  # No fields needed, just the endpoint is sufficient


class ContentItemResponse(BaseModel):
    """Response schema for a content item."""

    id: str
    title: str
    description: Optional[str]
    topic: str
    category: str
    status: str
    view_count: int
    engagement_metadata: Dict
    created_at: datetime
    published_at: Optional[datetime]
    updated_at: datetime
    tags: List[ContentTagResponse] = []

    class Config:
        from_attributes = True


class ContentItemListResponse(BaseModel):
    """Response schema for listing content items."""

    items: List[ContentItemResponse]
    total: int
    skip: int
    limit: int
