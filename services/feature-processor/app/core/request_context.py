"""Request context helpers for feature-processor HTTP endpoints."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from app.core.config import config
from fastapi import Request


@dataclass(frozen=True)
class RequestContext:
    """Request-scoped identifiers used for logging and tracing."""

    request_id: str
    correlation_id: str
    method: str
    path: str
    client_host: str | None

    def to_log_fields(self) -> dict[str, str | None]:
        """Return structured log fields for the request."""

        return {
            "request_id": self.request_id,
            "correlation_id": self.correlation_id,
            "http_method": self.method,
            "http_path": self.path,
            "client_host": self.client_host,
        }


def build_request_context(request: Request) -> RequestContext:
    """Build request context from incoming headers and request metadata."""

    request_id = request.headers.get(config.REQUEST_ID_HEADER) or str(uuid4())
    correlation_id = request.headers.get(config.CORRELATION_ID_HEADER) or request_id
    return RequestContext(
        request_id=request_id,
        correlation_id=correlation_id,
        method=request.method,
        path=request.url.path,
        client_host=request.client.host if request.client else None,
    )


def get_request_context(request: Request) -> RequestContext:
    """Return the current request context."""

    return request.state.request_context
