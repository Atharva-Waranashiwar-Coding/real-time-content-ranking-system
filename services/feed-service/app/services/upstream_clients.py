"""HTTP clients for upstream service integration used by feed-service."""

from __future__ import annotations

from typing import Protocol

from app.core import config
from app.schemas import (
    UpstreamContentItem,
    UpstreamContentListResponse,
    UpstreamUserResponse,
)

from shared_clients import ServiceClient
from shared_schemas import (
    ExperimentAssignmentV1Schema,
    ExperimentExposureCreateV1Schema,
    ExperimentExposureV1Schema,
    RankingRequestV1Schema,
    RankingResponseV1Schema,
)


class UserContextClientProtocol(Protocol):
    """Protocol for fetching user context needed for feed generation."""

    async def get_user(
        self,
        user_id: str,
        *,
        headers: dict[str, str] | None = None,
    ) -> UpstreamUserResponse:
        """Return a user and nested profile."""


class ContentCatalogClientProtocol(Protocol):
    """Protocol for fetching candidate content from content-service."""

    async def list_published_content(
        self,
        *,
        limit: int,
        topic: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> list[UpstreamContentItem]:
        """Return published content items."""


class RankingApiClientProtocol(Protocol):
    """Protocol for calling ranking-service."""

    async def rank_candidates(
        self,
        ranking_request: RankingRequestV1Schema,
        *,
        headers: dict[str, str],
    ) -> RankingResponseV1Schema:
        """Return ranked candidate content."""


class ExperimentationApiClientProtocol(Protocol):
    """Protocol for deterministic experiment assignment and exposure logging."""

    async def get_assignment(
        self,
        user_id: str,
        *,
        headers: dict[str, str],
    ) -> ExperimentAssignmentV1Schema:
        """Return the active experiment assignment for the user."""

    async def record_exposure(
        self,
        exposure_request: ExperimentExposureCreateV1Schema,
        *,
        headers: dict[str, str],
    ) -> ExperimentExposureV1Schema:
        """Persist an experiment exposure for the feed response."""


class UserContextClient:
    """HTTP client for user-service."""

    def __init__(self, base_url: str):
        self.base_url = base_url

    async def get_user(
        self,
        user_id: str,
        *,
        headers: dict[str, str] | None = None,
    ) -> UpstreamUserResponse:
        """Fetch a user and nested profile."""

        async with ServiceClient(
            self.base_url,
            caller_service=config.SERVICE_NAME,
            dependency_name="user-service",
        ) as client:
            response = await client.get(f"/api/v1/users/{user_id}", headers=headers)
            response.raise_for_status()
            return UpstreamUserResponse.model_validate(response.json())


class ContentCatalogClient:
    """HTTP client for content-service."""

    def __init__(self, base_url: str):
        self.base_url = base_url

    async def list_published_content(
        self,
        *,
        limit: int,
        topic: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> list[UpstreamContentItem]:
        """Fetch published content with an optional topic filter."""

        params = {"status": "published", "limit": limit, "skip": 0}
        if topic is not None:
            params["topic"] = topic

        async with ServiceClient(
            self.base_url,
            caller_service=config.SERVICE_NAME,
            dependency_name="content-service",
        ) as client:
            response = await client.get(
                "/api/v1/content",
                params=params,
                headers=headers,
            )
            response.raise_for_status()
            payload = UpstreamContentListResponse.model_validate(response.json())
            return payload.items


class RankingApiClient:
    """HTTP client for ranking-service."""

    def __init__(self, base_url: str):
        self.base_url = base_url

    async def rank_candidates(
        self,
        ranking_request: RankingRequestV1Schema,
        *,
        headers: dict[str, str],
    ) -> RankingResponseV1Schema:
        """Send candidates to ranking-service and return the scored response."""

        async with ServiceClient(
            self.base_url,
            caller_service=config.SERVICE_NAME,
            dependency_name="ranking-service",
        ) as client:
            response = await client.post(
                "/api/v1/rankings",
                json=ranking_request.model_dump(mode="json"),
                headers=headers,
            )
            response.raise_for_status()
            return RankingResponseV1Schema.model_validate(response.json())


class ExperimentationApiClient:
    """HTTP client for experimentation-service."""

    def __init__(self, base_url: str):
        self.base_url = base_url

    async def get_assignment(
        self,
        user_id: str,
        *,
        headers: dict[str, str],
    ) -> ExperimentAssignmentV1Schema:
        """Fetch the deterministic experiment assignment for a user."""

        async with ServiceClient(
            self.base_url,
            caller_service=config.SERVICE_NAME,
            dependency_name="experimentation-service",
        ) as client:
            response = await client.get(
                f"/api/v1/experiments/assignment?user_id={user_id}",
                headers=headers,
            )
            response.raise_for_status()
            return ExperimentAssignmentV1Schema.model_validate(response.json())

    async def record_exposure(
        self,
        exposure_request: ExperimentExposureCreateV1Schema,
        *,
        headers: dict[str, str],
    ) -> ExperimentExposureV1Schema:
        """Persist a feed exposure for the user's assigned experiment variant."""

        async with ServiceClient(
            self.base_url,
            caller_service=config.SERVICE_NAME,
            dependency_name="experimentation-service",
        ) as client:
            response = await client.post(
                "/api/v1/experiments/exposures",
                json=exposure_request.model_dump(mode="json"),
                headers=headers,
            )
            response.raise_for_status()
            return ExperimentExposureV1Schema.model_validate(response.json())


__all__ = [
    "ContentCatalogClient",
    "ContentCatalogClientProtocol",
    "ExperimentationApiClient",
    "ExperimentationApiClientProtocol",
    "RankingApiClient",
    "RankingApiClientProtocol",
    "UserContextClient",
    "UserContextClientProtocol",
]
