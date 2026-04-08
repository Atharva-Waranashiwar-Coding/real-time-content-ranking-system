"""Candidate retrieval logic for feed-service."""

from __future__ import annotations

from collections.abc import Iterable

from app.core.config import config
from app.schemas import UpstreamContentItem
from app.services.feature_store import FeedRedisStore
from app.services.upstream_clients import (
    ContentCatalogClientProtocol,
    UserContextClientProtocol,
)

from shared_schemas import RANKING_TOPICS, CandidateSource, RankingCandidateV1Schema


class CandidateService:
    """Retrieve and assemble feed candidates from recent, trending, and topical sources."""

    def __init__(
        self,
        *,
        content_client: ContentCatalogClientProtocol,
        user_client: UserContextClientProtocol,
        feature_store: FeedRedisStore,
    ):
        self.content_client = content_client
        self.user_client = user_client
        self.feature_store = feature_store

    async def retrieve_candidates(self, user_id: str) -> list[RankingCandidateV1Schema]:
        """Retrieve deduplicated feed candidates for a user."""

        effective_topic_affinity = await self._get_effective_topic_affinity(user_id)
        top_topics = [
            topic
            for topic, affinity_score in sorted(
                effective_topic_affinity.items(),
                key=lambda item: (item[1], item[0]),
                reverse=True,
            )
            if affinity_score > 0
        ][: config.FEED_MAX_TOPIC_SOURCES]

        recent_items = await self.content_client.list_published_content(
            limit=config.FEED_RECENT_CANDIDATE_LIMIT
        )
        trending_seed_items = await self.content_client.list_published_content(
            limit=config.FEED_TRENDING_SEED_LIMIT
        )

        topic_source_items: list[UpstreamContentItem] = []
        for topic in top_topics:
            topic_source_items.extend(
                await self.content_client.list_published_content(
                    limit=config.FEED_TOPIC_CANDIDATE_LIMIT,
                    topic=topic,
                )
            )

        unique_items_by_id = self._index_unique_items(
            recent_items,
            trending_seed_items,
            topic_source_items,
        )
        features_by_id = {
            content_id: await self.feature_store.read_content_features(
                content_id,
                topic=item.topic,
            )
            for content_id, item in unique_items_by_id.items()
        }

        source_map: dict[str, list[CandidateSource]] = {}
        self._apply_source(source_map, recent_items, CandidateSource.RECENT)

        trending_items = sorted(
            trending_seed_items,
            key=lambda item: (
                features_by_id[item.id].trending_score,
                item.published_at or item.created_at,
                item.id,
            ),
            reverse=True,
        )[: config.FEED_TRENDING_SOURCE_LIMIT]
        self._apply_source(source_map, trending_items, CandidateSource.TRENDING)
        self._apply_source(source_map, topic_source_items, CandidateSource.TOPIC_AFFINITY)

        return [
            RankingCandidateV1Schema(
                content_id=item.id,
                title=item.title,
                description=item.description,
                topic=item.topic,
                category=item.category,
                published_at=item.published_at,
                candidate_sources=source_map.get(content_id, []),
                user_topic_affinity=effective_topic_affinity.get(item.topic, 0.0),
                content_features=features_by_id[content_id],
            )
            for content_id, item in unique_items_by_id.items()
            if content_id in source_map
        ]

    async def _get_effective_topic_affinity(self, user_id: str) -> dict[str, float]:
        """Blend runtime topic affinity with profile preferences."""

        runtime_topic_affinity = await self.feature_store.read_user_topic_affinity(user_id)
        user = await self.user_client.get_user(user_id)
        profile_affinity = user.profile.topic_preferences if user.profile is not None else {}

        normalized_runtime_affinity = self._normalize_runtime_affinity(runtime_topic_affinity)
        effective_affinity: dict[str, float] = {}
        for topic in RANKING_TOPICS:
            runtime_score = normalized_runtime_affinity.get(topic, 0.0)
            profile_score = profile_affinity.get(topic, 0.0)
            if normalized_runtime_affinity:
                effective_affinity[topic] = round(
                    0.7 * runtime_score + 0.3 * profile_score,
                    6,
                )
            else:
                effective_affinity[topic] = round(profile_score, 6)
        return effective_affinity

    @staticmethod
    def _normalize_runtime_affinity(topic_affinity: dict[str, float]) -> dict[str, float]:
        """Normalize raw runtime affinity scores to a bounded 0..1 scale."""

        positive_values = [max(score, 0.0) for score in topic_affinity.values()]
        if not positive_values or max(positive_values) <= 0:
            return {}

        scale = max(positive_values)
        return {
            topic: round(max(score, 0.0) / scale, 6)
            for topic, score in topic_affinity.items()
            if topic in RANKING_TOPICS
        }

    @staticmethod
    def _index_unique_items(
        *content_groups: Iterable[UpstreamContentItem],
    ) -> dict[str, UpstreamContentItem]:
        """Index unique content items while preserving the first-seen order."""

        indexed_items: dict[str, UpstreamContentItem] = {}
        for content_group in content_groups:
            for item in content_group:
                indexed_items.setdefault(item.id, item)
        return indexed_items

    @staticmethod
    def _apply_source(
        source_map: dict[str, list[CandidateSource]],
        items: Iterable[UpstreamContentItem],
        source: CandidateSource,
    ) -> None:
        """Add a source label to each candidate in the source map."""

        for item in items:
            source_map.setdefault(item.id, [])
            if source not in source_map[item.id]:
                source_map[item.id].append(source)
