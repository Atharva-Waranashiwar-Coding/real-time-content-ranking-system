"""Business logic layer for content operations."""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from app.models import ContentItem, ContentTag
from app.schemas.content import (
    ContentTagRequest,
    ContentTagResponse,
    ContentItemCreateRequest,
    ContentItemUpdateRequest,
    ContentItemResponse,
    ContentItemListResponse,
)


class ContentService:
    """Service for content-related operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # Tag operations
    async def create_tag(self, request: ContentTagRequest) -> ContentTagResponse:
        """Create a new tag."""
        try:
            tag = ContentTag(name=request.name, description=request.description)
            self.session.add(tag)
            await self.session.commit()
            await self.session.refresh(tag)
            return ContentTagResponse.from_orm(tag)
        except IntegrityError as e:
            await self.session.rollback()
            if "name" in str(e.orig):
                raise ValueError(f"Tag '{request.name}' already exists")
            raise ValueError("Tag creation failed")

    async def get_tag_by_id(self, tag_id: str) -> Optional[ContentTagResponse]:
        """Retrieve a tag by ID."""
        query = select(ContentTag).where(ContentTag.id == tag_id)
        result = await self.session.execute(query)
        tag = result.scalars().first()
        return ContentTagResponse.from_orm(tag) if tag else None

    async def list_tags(self, skip: int = 0, limit: int = 100) -> List[ContentTagResponse]:
        """List all tags."""
        query = select(ContentTag).offset(skip).limit(limit)
        result = await self.session.execute(query)
        tags = result.scalars().all()
        return [ContentTagResponse.from_orm(t) for t in tags]

    # Content item operations
    async def create_content_item(self, request: ContentItemCreateRequest) -> ContentItemResponse:
        """Create a new content item."""
        # Create content item
        content = ContentItem(
            title=request.title,
            description=request.description,
            topic=request.topic,
            category=request.category.value,
            status="draft",
            engagement_metadata={},
        )
        self.session.add(content)
        await self.session.flush()

        # Attach tags if provided
        if request.tag_ids:
            tags_query = select(ContentTag).where(ContentTag.id.in_(request.tag_ids))
            tags_result = await self.session.execute(tags_query)
            tags = tags_result.scalars().all()
            for tag in tags:
                content.tags.append(tag)

        await self.session.commit()
        await self.session.refresh(content, ["tags"])
        return ContentItemResponse.from_orm(content)

    async def get_content_item(self, content_id: str) -> Optional[ContentItemResponse]:
        """Retrieve a content item by ID."""
        query = select(ContentItem).where(ContentItem.id == content_id).options(selectinload(ContentItem.tags))
        result = await self.session.execute(query)
        content = result.scalars().first()
        return ContentItemResponse.from_orm(content) if content else None

    async def update_content_item(
        self,
        content_id: str,
        request: ContentItemUpdateRequest,
    ) -> Optional[ContentItemResponse]:
        """Update a content item."""
        query = select(ContentItem).where(ContentItem.id == content_id).options(selectinload(ContentItem.tags))
        result = await self.session.execute(query)
        content = result.scalars().first()

        if not content:
            return None

        # Update fields
        if request.title:
            content.title = request.title
        if request.description is not None:
            content.description = request.description
        if request.topic:
            content.topic = request.topic
        if request.category:
            content.category = request.category.value

        # Update tags if provided
        if request.tag_ids is not None:
            tags_query = select(ContentTag).where(ContentTag.id.in_(request.tag_ids))
            tags_result = await self.session.execute(tags_query)
            tags = tags_result.scalars().all()
            content.tags = tags

        await self.session.commit()
        await self.session.refresh(content, ["tags"])
        return ContentItemResponse.from_orm(content)

    async def publish_content_item(self, content_id: str) -> Optional[ContentItemResponse]:
        """Publish a content item (draft -> published)."""
        query = select(ContentItem).where(ContentItem.id == content_id).options(selectinload(ContentItem.tags))
        result = await self.session.execute(query)
        content = result.scalars().first()

        if not content:
            return None

        content.status = "published"
        content.published_at = datetime.now(timezone.utc)

        await self.session.commit()
        await self.session.refresh(content, ["tags"])
        return ContentItemResponse.from_orm(content)

    async def list_content_items(
        self,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        status: Optional[str] = None,
        topic: Optional[str] = None,
    ) -> ContentItemListResponse:
        """List content items with optional filtering."""
        query = select(ContentItem).options(selectinload(ContentItem.tags))

        # Apply filters
        if category:
            query = query.where(ContentItem.category == category)
        if status:
            query = query.where(ContentItem.status == status)
        if topic:
            query = query.where(ContentItem.topic == topic)

        # Get total count
        count_query = select(ContentItem)
        if category:
            count_query = count_query.where(ContentItem.category == category)
        if status:
            count_query = count_query.where(ContentItem.status == status)
        if topic:
            count_query = count_query.where(ContentItem.topic == topic)
        
        count_result = await self.session.execute(count_query)
        total = len(count_result.scalars().all())

        # Get paginated results
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        items = result.scalars().all()

        return ContentItemListResponse(
            items=[ContentItemResponse.from_orm(item) for item in items],
            total=total,
            skip=skip,
            limit=limit,
        )

    async def delete_content_item(self, content_id: str) -> bool:
        """Delete a content item."""
        query = select(ContentItem).where(ContentItem.id == content_id)
        result = await self.session.execute(query)
        content = result.scalars().first()

        if not content:
            return False

        await self.session.delete(content)
        await self.session.commit()
        return True
