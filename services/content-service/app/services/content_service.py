"""Business logic layer for content operations."""

from __future__ import annotations

from datetime import datetime, timezone

from app.models import ContentItem, ContentTag
from app.schemas.content import (
    ContentItemCreateRequest,
    ContentItemListResponse,
    ContentItemResponse,
    ContentItemUpdateRequest,
    ContentTagRequest,
    ContentTagResponse,
)
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from shared_schemas import ContentStatus


class ContentService:
    """Service for content-related operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_tag(self, request: ContentTagRequest) -> ContentTagResponse:
        """Create a new tag."""

        try:
            tag = ContentTag(name=request.name, description=request.description)
            self.session.add(tag)
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            if "name" in str(exc.orig).lower():
                raise ValueError(f"Tag '{request.name}' already exists") from exc
            raise ValueError("Tag creation failed") from exc

        created_tag = await self._get_tag_model(tag.id)
        return self._serialize_tag(created_tag)

    async def get_tag_by_id(self, tag_id: str) -> ContentTagResponse | None:
        """Retrieve a tag by ID."""

        tag = await self._get_tag_model(tag_id)
        return self._serialize_tag(tag) if tag else None

    async def list_tags(self, skip: int = 0, limit: int = 100) -> list[ContentTagResponse]:
        """List all tags."""

        query = select(ContentTag).order_by(ContentTag.name.asc()).offset(skip).limit(limit)
        result = await self.session.execute(query)
        tags = result.scalars().all()
        return [self._serialize_tag(tag) for tag in tags]

    async def create_content_item(self, request: ContentItemCreateRequest) -> ContentItemResponse:
        """Create a new content item."""

        tags = await self._get_tags_by_ids(request.tag_ids)
        status = request.status.value
        published_at = self._utc_now() if request.status == ContentStatus.PUBLISHED else None

        content = ContentItem(
            title=request.title,
            description=request.description,
            topic=request.topic,
            category=request.category.value,
            status=status,
            published_at=published_at,
            engagement_metadata=self._default_engagement_metadata(),
        )
        content.tags = tags

        self.session.add(content)
        await self.session.commit()

        created_content = await self._get_content_model(content.id)
        return self._serialize_content(created_content)

    async def get_content_item(self, content_id: str) -> ContentItemResponse | None:
        """Retrieve a content item by ID."""

        content = await self._get_content_model(content_id)
        return self._serialize_content(content) if content else None

    async def update_content_item(
        self,
        content_id: str,
        request: ContentItemUpdateRequest,
    ) -> ContentItemResponse | None:
        """Update a content item."""

        content = await self._get_content_model(content_id)
        if not content:
            return None

        if "title" in request.model_fields_set and request.title is not None:
            content.title = request.title
        if "description" in request.model_fields_set:
            content.description = request.description
        if "topic" in request.model_fields_set and request.topic is not None:
            content.topic = request.topic
        if "category" in request.model_fields_set and request.category is not None:
            content.category = request.category.value
        if "status" in request.model_fields_set and request.status is not None:
            self._apply_status_transition(content, request.status)
        if "tag_ids" in request.model_fields_set and request.tag_ids is not None:
            content.tags = await self._get_tags_by_ids(request.tag_ids)

        await self.session.commit()
        refreshed_content = await self._get_content_model(content_id)
        return self._serialize_content(refreshed_content)

    async def publish_content_item(self, content_id: str) -> ContentItemResponse | None:
        """Publish a content item."""

        content = await self._get_content_model(content_id)
        if not content:
            return None

        self._apply_status_transition(content, ContentStatus.PUBLISHED)
        await self.session.commit()

        refreshed_content = await self._get_content_model(content_id)
        return self._serialize_content(refreshed_content)

    async def list_content_items(
        self,
        skip: int = 0,
        limit: int = 100,
        category: str | None = None,
        status: str | None = None,
        topic: str | None = None,
        tag: str | None = None,
    ) -> ContentItemListResponse:
        """List content items with optional filtering."""

        normalized_tag = tag.strip().lower() if tag else None
        normalized_topic = topic.strip().lower() if topic else None

        query = select(ContentItem).options(selectinload(ContentItem.tags))
        count_query = select(func.count(func.distinct(ContentItem.id))).select_from(ContentItem)

        if normalized_tag:
            query = query.join(ContentItem.tags).where(ContentTag.name == normalized_tag)
            count_query = count_query.join(ContentItem.tags).where(ContentTag.name == normalized_tag)
        if category:
            query = query.where(ContentItem.category == category)
            count_query = count_query.where(ContentItem.category == category)
        if status:
            query = query.where(ContentItem.status == status)
            count_query = count_query.where(ContentItem.status == status)
        if normalized_topic:
            query = query.where(ContentItem.topic == normalized_topic)
            count_query = count_query.where(ContentItem.topic == normalized_topic)

        total = (await self.session.execute(count_query)).scalar_one()

        ordered_query = (
            query
            .distinct()
            .order_by(ContentItem.published_at.desc().nullslast(), ContentItem.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(ordered_query)
        items = result.scalars().all()

        return ContentItemListResponse(
            items=[self._serialize_content(item) for item in items],
            total=total,
            skip=skip,
            limit=limit,
        )

    async def delete_content_item(self, content_id: str) -> bool:
        """Delete a content item."""

        content = await self._get_content_model(content_id)
        if not content:
            return False

        await self.session.delete(content)
        await self.session.commit()
        return True

    async def _get_content_model(self, content_id: str) -> ContentItem | None:
        """Retrieve a content model with tags preloaded."""

        query = (
            select(ContentItem)
            .where(ContentItem.id == content_id)
            .options(selectinload(ContentItem.tags))
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def _get_tag_model(self, tag_id: str) -> ContentTag | None:
        """Retrieve a content tag model."""

        query = select(ContentTag).where(ContentTag.id == tag_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def _get_tags_by_ids(self, tag_ids: list[str]) -> list[ContentTag]:
        """Fetch and validate content tags by identifier."""

        if not tag_ids:
            return []

        unique_tag_ids = list(dict.fromkeys(tag_ids))
        query = select(ContentTag).where(ContentTag.id.in_(unique_tag_ids))
        result = await self.session.execute(query)
        tags = result.scalars().all()

        found_tag_ids = {tag.id for tag in tags}
        missing_tag_ids = [tag_id for tag_id in unique_tag_ids if tag_id not in found_tag_ids]
        if missing_tag_ids:
            missing = ", ".join(missing_tag_ids)
            raise ValueError(f"Unknown tag IDs: {missing}")

        tags_by_id = {tag.id: tag for tag in tags}
        return [tags_by_id[tag_id] for tag_id in unique_tag_ids]

    def _apply_status_transition(self, content: ContentItem, status: ContentStatus) -> None:
        """Apply consistent draft/published state transitions."""

        content.status = status.value
        if status == ContentStatus.PUBLISHED and content.published_at is None:
            content.published_at = self._utc_now()
        if status == ContentStatus.DRAFT:
            content.published_at = None

    @staticmethod
    def _serialize_tag(tag: ContentTag) -> ContentTagResponse:
        """Convert ORM tag models to response schemas."""

        return ContentTagResponse.model_validate(tag)

    @staticmethod
    def _serialize_content(content: ContentItem) -> ContentItemResponse:
        """Convert ORM content models to response schemas."""

        return ContentItemResponse.model_validate(content)

    @staticmethod
    def _default_engagement_metadata() -> dict[str, int]:
        """Return the baseline engagement counters for new content."""

        return {
            "impressions": 0,
            "clicks": 0,
            "likes": 0,
            "saves": 0,
            "skips": 0,
        }

    @staticmethod
    def _utc_now() -> datetime:
        """Return the current UTC timestamp."""

        return datetime.now(timezone.utc)
