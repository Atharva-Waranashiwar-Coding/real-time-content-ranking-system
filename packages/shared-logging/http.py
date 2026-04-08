"""Shared HTTP middleware utilities for request telemetry."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable, Iterable
from time import perf_counter
from typing import Any

from fastapi import FastAPI, Request, Response

from .metrics import observe_http_request

DEFAULT_QUIET_PATHS = frozenset(
    {
        "/",
        "/metrics",
        "/api/v1/health",
        "/api/v1/ready",
        "/api/v1/live",
    }
)


def _resolve_path_template(request: Request) -> str:
    """Resolve the matched route template, falling back to the raw path."""

    route = request.scope.get("route")
    route_path = getattr(route, "path", None)
    if isinstance(route_path, str):
        return route_path
    return request.url.path


def install_http_observability(
    app: FastAPI,
    *,
    service_name: str,
    logger: logging.Logger,
    build_request_context: Callable[[Request], Any],
    request_id_header: str,
    correlation_id_header: str,
    quiet_paths: Iterable[str] = DEFAULT_QUIET_PATHS,
) -> None:
    """Install request context propagation, structured logs, and HTTP metrics."""

    quiet_path_set = set(quiet_paths)

    @app.middleware("http")
    async def observability_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_context = build_request_context(request)
        request.state.request_context = request_context

        started_at = perf_counter()
        response: Response | None = None
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            duration_seconds = perf_counter() - started_at
            path = _resolve_path_template(request)
            if path not in quiet_path_set:
                observe_http_request(
                    service_name=service_name,
                    method=request.method,
                    path=path,
                    status_code=status_code,
                    duration_seconds=duration_seconds,
                )
                logger.exception(
                    "HTTP request failed",
                    extra={
                        **request_context.to_log_fields(),
                        "status_code": status_code,
                        "duration_ms": round(duration_seconds * 1000, 3),
                    },
                )
            raise

        duration_seconds = perf_counter() - started_at
        response.headers[request_id_header] = request_context.request_id
        response.headers[correlation_id_header] = request_context.correlation_id

        path = _resolve_path_template(request)
        if path not in quiet_path_set:
            observe_http_request(
                service_name=service_name,
                method=request.method,
                path=path,
                status_code=status_code,
                duration_seconds=duration_seconds,
            )
            logger.info(
                "HTTP request completed",
                extra={
                    **request_context.to_log_fields(),
                    "status_code": status_code,
                    "duration_ms": round(duration_seconds * 1000, 3),
                },
            )

        return response


__all__ = ["DEFAULT_QUIET_PATHS", "install_http_observability"]
