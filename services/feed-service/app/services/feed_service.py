"""Feed assembly logic for feed-service."""

from __future__ import annotations

import logging
from time import perf_counter

from app.core import RequestContext, config
from app.schemas import FeedQueryParams, FeedResponse
from app.services.candidate_service import CandidateService
from app.services.feature_store import FeedRedisStore
from app.services.upstream_clients import (
    ExperimentationApiClientProtocol,
    RankingApiClientProtocol,
)
from httpx import HTTPError

from shared_logging import observe_feed_assembly_duration
from shared_schemas import (
    ExperimentExposureCreateV1Schema,
    ExperimentExposureItemV1Schema,
    RankingRequestV1Schema,
)

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
        experimentation_client: ExperimentationApiClientProtocol,
        feature_store: FeedRedisStore,
        cache_ttl_seconds: int,
    ):
        self.candidate_service = candidate_service
        self.ranking_client = ranking_client
        self.experimentation_client = experimentation_client
        self.feature_store = feature_store
        self.cache_ttl_seconds = cache_ttl_seconds

    async def get_feed(
        self,
        query_params: FeedQueryParams,
        request_context: RequestContext,
    ) -> FeedResponse:
        """Return a paginated personalized feed for a user."""

        started_at = perf_counter()
        headers = {
            config.REQUEST_ID_HEADER: request_context.request_id,
            config.CORRELATION_ID_HEADER: request_context.correlation_id,
        }
        try:
            experiment_assignment = await self.experimentation_client.get_assignment(
                str(query_params.user_id),
                headers=headers,
            )
        except HTTPError as exc:
            raise FeedAssemblyError(
                "Experiment assignment retrieval failed during feed assembly"
            ) from exc

        cached_payload = await self.feature_store.get_cached_feed(
            str(query_params.user_id),
            experiment_assignment.experiment_key,
            experiment_assignment.variant_key,
            query_params.limit,
            query_params.offset,
        )
        if cached_payload is not None:
            cached_feed = FeedResponse.model_validate(cached_payload)
            cached_feed = cached_feed.model_copy(
                update={
                    "cache_hit": True,
                    "experiment_assignment": experiment_assignment,
                }
            )
            delivered_feed = await self._record_exposure(
                cached_feed,
                session_id=query_params.session_id,
                request_context=request_context,
            )
            observe_feed_assembly_duration(
                service_name=config.SERVICE_NAME,
                cache_hit=True,
                duration_seconds=perf_counter() - started_at,
            )
            return delivered_feed

        try:
            candidates = await self.candidate_service.get_candidates(
                str(query_params.user_id),
                headers=headers,
            )
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
                experiment_assignment=experiment_assignment,
            )
            await self.feature_store.set_cached_feed(
                str(query_params.user_id),
                experiment_assignment.experiment_key,
                experiment_assignment.variant_key,
                query_params.limit,
                query_params.offset,
                empty_feed.model_dump(mode="json"),
                self.cache_ttl_seconds,
            )
            delivered_feed = await self._record_exposure(
                empty_feed,
                session_id=query_params.session_id,
                request_context=request_context,
            )
            observe_feed_assembly_duration(
                service_name=config.SERVICE_NAME,
                cache_hit=False,
                duration_seconds=perf_counter() - started_at,
            )
            return delivered_feed

        ranking_request = RankingRequestV1Schema(
            user_id=query_params.user_id,
            strategy_name=experiment_assignment.strategy_name,
            candidates=candidates,
            apply_diversity_penalty=True,
            metadata={
                "surface": "home_feed",
                "feed_limit": query_params.limit,
                "feed_offset": query_params.offset,
                "experiment_key": experiment_assignment.experiment_key,
                "variant_key": experiment_assignment.variant_key,
            },
        )

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
            experiment_assignment=experiment_assignment,
            generated_at=ranking_response.generated_at,
        )

        await self.feature_store.set_cached_feed(
            str(query_params.user_id),
            experiment_assignment.experiment_key,
            experiment_assignment.variant_key,
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
                "experiment_key": experiment_assignment.experiment_key,
                "variant_key": experiment_assignment.variant_key,
                "strategy_name": experiment_assignment.strategy_name,
            },
        )
        delivered_feed = await self._record_exposure(
            feed_response,
            session_id=query_params.session_id,
            request_context=request_context,
        )
        observe_feed_assembly_duration(
            service_name=config.SERVICE_NAME,
            cache_hit=False,
            duration_seconds=perf_counter() - started_at,
        )
        return delivered_feed

    async def _record_exposure(
        self,
        feed_response: FeedResponse,
        *,
        session_id: str | None,
        request_context: RequestContext,
    ) -> FeedResponse:
        """Persist an experiment exposure for the returned feed response."""

        if feed_response.experiment_assignment is None:
            return feed_response

        exposure_request = ExperimentExposureCreateV1Schema(
            experiment_key=feed_response.experiment_assignment.experiment_key,
            variant_key=feed_response.experiment_assignment.variant_key,
            strategy_name=feed_response.experiment_assignment.strategy_name,
            user_id=feed_response.user_id,
            session_id=session_id,
            feed_limit=feed_response.limit,
            feed_offset=feed_response.offset,
            cache_hit=feed_response.cache_hit,
            generated_at=feed_response.generated_at,
            items=[
                ExperimentExposureItemV1Schema(
                    content_id=item.content_id,
                    rank=item.rank,
                    score=item.score,
                    topic=item.topic,
                    category=item.category,
                )
                for item in feed_response.items
            ],
        )
        headers = {
            config.REQUEST_ID_HEADER: request_context.request_id,
            config.CORRELATION_ID_HEADER: request_context.correlation_id,
        }

        try:
            exposure = await self.experimentation_client.record_exposure(
                exposure_request,
                headers=headers,
            )
        except HTTPError as exc:
            raise FeedAssemblyError(
                "Experiment exposure logging failed during feed delivery"
            ) from exc

        return feed_response.model_copy(update={"exposure_id": exposure.exposure_id})
