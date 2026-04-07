"""API routes for content endpoints."""

from app.db import get_db
from app.schemas.content import (
    ContentItemCreateRequest,
    ContentItemListResponse,
    ContentItemResponse,
    ContentItemUpdateRequest,
    ContentTagRequest,
    ContentTagResponse,
)
from app.services import ContentService
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from shared_schemas import ContentCategory, ContentStatus

router = APIRouter(prefix="/api/v1", tags=["content"])


def _raise_bad_request(detail: str) -> None:
    """Raise a standard 400 API error."""

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def _raise_not_found(resource_name: str, resource_id: str) -> None:
    """Raise a standard 404 API error."""

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{resource_name} '{resource_id}' not found",
    )


@router.get("/tags", response_model=list[ContentTagResponse])
async def list_tags(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
) -> list[ContentTagResponse]:
    """List all tags."""
    service = ContentService(db)
    return await service.list_tags(skip=skip, limit=limit)


@router.post("/tags", response_model=ContentTagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    request: ContentTagRequest,
    db: AsyncSession = Depends(get_db),
) -> ContentTagResponse:
    """Create a new tag."""
    service = ContentService(db)
    try:
        return await service.create_tag(request)
    except ValueError as e:
        _raise_bad_request(str(e))


@router.get("/tags/{tag_id}", response_model=ContentTagResponse)
async def get_tag(
    tag_id: str,
    db: AsyncSession = Depends(get_db),
) -> ContentTagResponse:
    """Retrieve a tag by ID."""
    service = ContentService(db)
    tag = await service.get_tag_by_id(tag_id)
    if not tag:
        _raise_not_found("Tag", tag_id)
    return tag


@router.post("/content", response_model=ContentItemResponse, status_code=status.HTTP_201_CREATED)
async def create_content(
    request: ContentItemCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> ContentItemResponse:
    """Create a new content item."""
    service = ContentService(db)
    try:
        return await service.create_content_item(request)
    except ValueError as e:
        _raise_bad_request(str(e))


@router.get("/content", response_model=ContentItemListResponse)
async def list_content(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: ContentCategory | None = Query(None),
    status_value: ContentStatus | None = Query(None, alias="status"),
    topic: str | None = Query(None),
    tag: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> ContentItemListResponse:
    """List content items with optional filtering."""
    service = ContentService(db)
    return await service.list_content_items(
        skip=skip,
        limit=limit,
        category=category.value if category else None,
        status=status_value.value if status_value else None,
        topic=topic,
        tag=tag,
    )


@router.get("/content/{content_id}", response_model=ContentItemResponse)
async def get_content(
    content_id: str,
    db: AsyncSession = Depends(get_db),
) -> ContentItemResponse:
    """Retrieve a content item by ID."""
    service = ContentService(db)
    content = await service.get_content_item(content_id)
    if not content:
        _raise_not_found("Content", content_id)
    return content


@router.put("/content/{content_id}", response_model=ContentItemResponse)
async def update_content(
    content_id: str,
    request: ContentItemUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> ContentItemResponse:
    """Update a content item."""
    service = ContentService(db)
    try:
        updated_content = await service.update_content_item(content_id, request)
        if not updated_content:
            _raise_not_found("Content", content_id)
        return updated_content
    except ValueError as e:
        _raise_bad_request(str(e))


@router.post("/content/{content_id}/publish", response_model=ContentItemResponse)
async def publish_content(
    content_id: str,
    db: AsyncSession = Depends(get_db),
) -> ContentItemResponse:
    """Publish a content item."""
    service = ContentService(db)
    published_content = await service.publish_content_item(content_id)
    if not published_content:
        _raise_not_found("Content", content_id)
    return published_content


@router.delete("/content/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content(
    content_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a content item."""
    service = ContentService(db)
    success = await service.delete_content_item(content_id)
    if not success:
        _raise_not_found("Content", content_id)
