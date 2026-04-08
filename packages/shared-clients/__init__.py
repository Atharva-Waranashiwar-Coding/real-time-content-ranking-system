"""Shared HTTP and Kafka client utilities for the ranking platform."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any, Protocol

import httpx


async def create_http_client(timeout: float = 10.0) -> httpx.AsyncClient:
    """Create an async HTTP client."""

    return httpx.AsyncClient(timeout=timeout)


class ServiceClient:
    """Base client for inter-service HTTP communication."""

    def __init__(self, base_url: str, timeout: float = 10.0):
        """Initialize a service client."""

        self.base_url = base_url
        self.timeout = timeout
        self.client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> ServiceClient:
        """Async context manager entry."""

        self.client = await create_http_client(self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""

        if self.client:
            await self.client.aclose()

    async def get(self, path: str, **kwargs: Any) -> httpx.Response:
        """Make a GET request."""

        if not self.client:
            raise RuntimeError("Client not initialized. Use async context manager.")
        return await self.client.get(f"{self.base_url}{path}", **kwargs)

    async def post(self, path: str, **kwargs: Any) -> httpx.Response:
        """Make a POST request."""

        if not self.client:
            raise RuntimeError("Client not initialized. Use async context manager.")
        return await self.client.post(f"{self.base_url}{path}", **kwargs)


class KafkaProducerError(RuntimeError):
    """Raised when a Kafka publish attempt fails."""


@dataclass(frozen=True)
class KafkaMessage:
    """Structured Kafka message envelope."""

    topic: str
    value: dict[str, Any]
    key: str | None = None
    headers: dict[str, str] = field(default_factory=dict)


class KafkaProducer(Protocol):
    """Protocol used by services that publish Kafka events."""

    async def publish(self, message: KafkaMessage) -> None:
        """Publish a message to Kafka."""

    async def close(self) -> None:
        """Flush and close producer resources."""


class ConfluentKafkaProducer:
    """Async wrapper around the Confluent Kafka producer."""

    def __init__(
        self,
        bootstrap_servers: str,
        client_id: str,
        delivery_timeout_ms: int = 5000,
        flush_timeout_seconds: float = 5.0,
        extra_config: dict[str, Any] | None = None,
    ):
        """Initialize the producer with conservative defaults."""

        from confluent_kafka import Producer

        producer_config: dict[str, Any] = {
            "bootstrap.servers": bootstrap_servers,
            "client.id": client_id,
            "acks": "all",
            "enable.idempotence": True,
            "message.timeout.ms": delivery_timeout_ms,
        }
        if extra_config:
            producer_config.update(extra_config)

        self._producer = Producer(producer_config)
        self._flush_timeout_seconds = flush_timeout_seconds

    async def publish(self, message: KafkaMessage) -> None:
        """Publish a message and wait for delivery confirmation."""

        await asyncio.to_thread(self._publish_sync, message)

    async def close(self) -> None:
        """Flush producer buffers on shutdown."""

        await asyncio.to_thread(self._producer.flush, self._flush_timeout_seconds)

    def _publish_sync(self, message: KafkaMessage) -> None:
        """Perform the blocking Kafka publish."""

        delivery_error: Exception | None = None

        def delivery_callback(err, _msg) -> None:
            nonlocal delivery_error
            if err is not None:
                delivery_error = err

        payload = json.dumps(
            message.value,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        headers = [(key, value.encode("utf-8")) for key, value in message.headers.items()]

        try:
            self._producer.produce(
                topic=message.topic,
                key=message.key,
                value=payload,
                headers=headers,
                on_delivery=delivery_callback,
            )
            self._producer.flush(self._flush_timeout_seconds)
        except Exception as exc:  # pragma: no cover - underlying library error surface
            raise KafkaProducerError(f"Failed to publish Kafka message to {message.topic}") from exc

        if delivery_error is not None:
            raise KafkaProducerError(
                f"Kafka delivery failed for topic {message.topic}: {delivery_error}"
            )


def create_kafka_producer(
    bootstrap_servers: str,
    client_id: str,
    extra_config: dict[str, Any] | None = None,
) -> KafkaProducer:
    """Create the default Kafka producer implementation."""

    return ConfluentKafkaProducer(
        bootstrap_servers=bootstrap_servers,
        client_id=client_id,
        extra_config=extra_config,
    )


__all__ = [
    "ConfluentKafkaProducer",
    "KafkaMessage",
    "KafkaProducer",
    "KafkaProducerError",
    "ServiceClient",
    "create_http_client",
    "create_kafka_producer",
]
