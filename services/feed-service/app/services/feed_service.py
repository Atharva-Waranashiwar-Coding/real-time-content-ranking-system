"""Feed assembly logic for feed-service."""

from __future__ import annotations

import logging

from app.core import RequestContext, config
from app.schemas import FeedQueryParams, FeedResponse
from app.services.candidate_service import CandidateService
from app.services.feature_store import FeedRedisStore
from app.services.upstream_clients import RankingApiClientProtocol
from httpx import HTTPError

from shared_schemas import RankingRequestV1Schema

logger = logging.getLogger(config.SERVICE_NAME)


class FeedAssemblyError(RuntimeError):
    """Raised when feed assembly fails due to an upstream dependency."""


class FeedService:
    """Service that assembles, ranks, paginates, and caches user feeds."""

    def __init__(
        self,
        *,
        candidate_service: CandidateService,
        ranking_client: RankingApiClientProtocol,
        feature_store: FeedRedisStore,
        cache_ttl_seconds: int,
    ):
        self.candidate_service = candidate_service
        self.ranking_client = ranking_client
        self.feature_store = feature_store
        self.cache_ttl_seconds = cache_ttl_seconds

    async def get_feed(
        self,
        query_params: FeedQueryParams,
        request_context: RequestContext,
    ) -> FeedResponse:
        """Return a paginated personalized feed for a user."""

        cached_payload = await self.feature_store.get_cached_feed(
            str(query_params.user_id),
            query_params.limit,
            query_params.offset,
        )
        if cached_payload is not None:
            cached_feed = FeedResponse.model_validate(cached_payload)
            return cached_feed.model_copy(update={"cache_hit": True})

        try:
            candidates = await self.candidate_service.retrieve_candidates(str(query_params.user_id))
        except HTTPError as exc:
            raise FeedAssemblyError(
                "Feed candidate retrieval failed due to an upstream dependency"
            ) from exc

        if not candidates:
            empty_feed = FeedResponse(
                user_id=query_params.user_id,
                items=[],
                total_candidates=0,
                limit=query_params.limit,
                offset=query_params.offset,
                has_more=False,
                cache_hit=False,
            )
            await self.feature_store.set_cached_feed(
                str(query_params.user_id),
                query_params.limit,
                query_params.offset,
                empty_feed.model_dump(mode="json"),
                self.cache_ttl_seconds,
            )
            return empty_feed

        ranking_request = RankingRequestV1Schema(
            user_id=query_params.user_id,
            candidates=candidates,
            apply_diversity_penalty=True,
            metadata={
                "surface": "home_feed",
                "feed_limit": query_params.limit,
                "feed_offset": query_params.offset,
            },
        )
        headers = {
            config.REQUEST_ID_HEADER: request_context.request_id,
            config.CORRELATION_ID_HEADER: request_context.correlation_id,
        }

        try:
            ranking_response = await self.ranking_client.rank_candidates(
                ranking_request,
                headers=headers,
            )
        except HTTPError as exc:
            raise FeedAssemblyError("Ranking-service request failed during feed assembly") from exc

        paginated_items = ranking_response.ranked_items[
            query_params.offset : query_params.offset + query_params.limit
        ]
        feed_response = FeedResponse(
            user_id=query_params.user_id,
            items=paginated_items,
            total_candidates=ranking_response.candidate_count,
            limit=query_params.limit,
            offset=query_params.offset,
            has_more=(
                query_params.offset + query_params.limit
                < len(ranking_response.ranked_items)
            ),
            cache_hit=False,
            generated_at=ranking_response.generated_at,
        )

        await self.feature_store.set_cached_feed(
            str(query_params.user_id),
            query_params.limit,
            query_params.offset,
            feed_response.model_dump(mode="json"),
            self.cache_ttl_seconds,
        )

        logger.info(
            "Feed assembled successfully",
            extra={
                **request_context.to_log_fields(),
                "user_id": str(query_params.user_id),
                "candidate_count": ranking_response.candidate_count,
                "returned_count": len(paginated_items),
                "cache_hit": False,
            },
        )
        return feed_response
