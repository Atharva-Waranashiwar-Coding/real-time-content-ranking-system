"""API routes for content endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.services import ContentService
from app.schemas.content import (
    ContentTagRequest,
    ContentTagResponse,
    ContentItemCreateRequest,
    ContentItemUpdateRequest,
    ContentItemPublishRequest,
    ContentItemResponse,
    ContentItemListResponse,
)

router = APIRouter(prefix="/api/v1", tags=["content"])


# Tag endpoints
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/tags/{tag_id}", response_model=ContentTagResponse)
async def get_tag(
    tag_id: str,
    db: AsyncSession = Depends(get_db),
) -> ContentTagResponse:
    """Retrieve a tag by ID."""
    service = ContentService(db)
    tag = await service.get_tag_by_id(tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with ID '{tag_id}' not found",
        )
    return tag


# Content item endpoints
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/content", response_model=ContentItemListResponse)
async def list_content(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: str = Query(None),
    status: str = Query(None),
    topic: str = Query(None),
    db: AsyncSession = Depends(get_db),
) -> ContentItemListResponse:
    """List content items with optional filtering."""
    service = ContentService(db)
    return await service.list_content_items(
        skip=skip,
        limit=limit,
        category=category,
        status=status,
        topic=topic,
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content with ID '{content_id}' not found",
        )
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Content with ID '{content_id}' not found",
            )
        return updated_content
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/content/{content_id}/publish", response_model=ContentItemResponse)
async def publish_content(
    content_id: str,
    request: ContentItemPublishRequest,
    db: AsyncSession = Depends(get_db),
) -> ContentItemResponse:
    """Publish a content item (draft -> published)."""
    service = ContentService(db)
    published_content = await service.publish_content_item(content_id)
    if not published_content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content with ID '{content_id}' not found",
        )
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content with ID '{content_id}' not found",
        )
