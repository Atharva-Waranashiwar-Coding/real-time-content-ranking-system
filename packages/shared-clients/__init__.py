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


class KafkaConsumerError(RuntimeError):
    """Raised when a Kafka consume or commit attempt fails."""


@dataclass(frozen=True)
class KafkaMessage:
    """Structured Kafka message envelope."""

    topic: str
    value: dict[str, Any]
    key: str | None = None
    headers: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class KafkaRecord:
    """Structured Kafka record envelope returned by consumers."""

    topic: str
    value: dict[str, Any]
    key: str | None = None
    headers: dict[str, str] = field(default_factory=dict)
    partition: int | None = None
    offset: int | None = None
    timestamp_ms: int | None = None


class KafkaProducer(Protocol):
    """Protocol used by services that publish Kafka events."""

    async def publish(self, message: KafkaMessage) -> None:
        """Publish a message to Kafka."""

    async def close(self) -> None:
        """Flush and close producer resources."""


class KafkaConsumer(Protocol):
    """Protocol used by services that consume Kafka events."""

    async def poll(self, timeout_seconds: float = 1.0) -> KafkaRecord | None:
        """Poll for the next available Kafka record."""

    async def commit(self, record: KafkaRecord) -> None:
        """Commit the offset for a successfully processed Kafka record."""

    async def close(self) -> None:
        """Close consumer resources."""


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


class ConfluentKafkaConsumer:
    """Async wrapper around the Confluent Kafka consumer."""

    def __init__(
        self,
        bootstrap_servers: str,
        client_id: str,
        group_id: str,
        topics: list[str],
        auto_offset_reset: str = "latest",
        extra_config: dict[str, Any] | None = None,
    ):
        """Initialize the consumer with explicit group and topic configuration."""

        from confluent_kafka import Consumer

        consumer_config: dict[str, Any] = {
            "bootstrap.servers": bootstrap_servers,
            "client.id": client_id,
            "group.id": group_id,
            "auto.offset.reset": auto_offset_reset,
            "enable.auto.commit": False,
        }
        if extra_config:
            consumer_config.update(extra_config)

        self._consumer = Consumer(consumer_config)
        self._consumer.subscribe(topics)
        self._raw_messages: dict[tuple[str, int | None, int | None], Any] = {}

    async def poll(self, timeout_seconds: float = 1.0) -> KafkaRecord | None:
        """Poll for a single Kafka record."""

        return await asyncio.to_thread(self._poll_sync, timeout_seconds)

    async def commit(self, record: KafkaRecord) -> None:
        """Commit the offset of the provided record."""

        await asyncio.to_thread(self._commit_sync, record)

    async def close(self) -> None:
        """Close the underlying consumer."""

        await asyncio.to_thread(self._consumer.close)

    def _poll_sync(self, timeout_seconds: float) -> KafkaRecord | None:
        """Perform the blocking Kafka poll."""

        message = self._consumer.poll(timeout_seconds)
        if message is None:
            return None
        if message.error() is not None:
            raise KafkaConsumerError(f"Kafka consume failed: {message.error()}")

        raw_value = message.value()
        if raw_value is None:
            raise KafkaConsumerError("Kafka record did not include a payload")

        try:
            payload = json.loads(raw_value.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise KafkaConsumerError("Kafka record payload was not valid JSON") from exc

        raw_key = message.key()
        headers: dict[str, str] = {}
        for header_key, header_value in message.headers() or []:
            if isinstance(header_value, (bytes, bytearray)):
                headers[header_key] = header_value.decode("utf-8")
            elif header_value is None:
                headers[header_key] = ""
            else:
                headers[header_key] = str(header_value)

        record = KafkaRecord(
            topic=message.topic(),
            key=raw_key.decode("utf-8") if isinstance(raw_key, (bytes, bytearray)) else raw_key,
            value=payload,
            headers=headers,
            partition=message.partition(),
            offset=message.offset(),
            timestamp_ms=message.timestamp()[1],
        )
        self._raw_messages[(record.topic, record.partition, record.offset)] = message
        return record

    def _commit_sync(self, record: KafkaRecord) -> None:
        """Perform the blocking commit for a consumed record."""

        raw_message = self._raw_messages.pop(
            (record.topic, record.partition, record.offset),
            None,
        )
        if raw_message is None:
            raise KafkaConsumerError(
                "Kafka record could not be committed because its raw message is unavailable"
            )

        try:
            self._consumer.commit(message=raw_message, asynchronous=False)
        except Exception as exc:  # pragma: no cover - underlying library error surface
            raise KafkaConsumerError(
                f"Failed to commit Kafka offset for topic {record.topic}"
            ) from exc


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


def create_kafka_consumer(
    bootstrap_servers: str,
    client_id: str,
    group_id: str,
    topics: list[str],
    auto_offset_reset: str = "latest",
    extra_config: dict[str, Any] | None = None,
) -> KafkaConsumer:
    """Create the default Kafka consumer implementation."""

    return ConfluentKafkaConsumer(
        bootstrap_servers=bootstrap_servers,
        client_id=client_id,
        group_id=group_id,
        topics=topics,
        auto_offset_reset=auto_offset_reset,
        extra_config=extra_config,
    )


__all__ = [
    "ConfluentKafkaConsumer",
    "ConfluentKafkaProducer",
    "KafkaConsumer",
    "KafkaConsumerError",
    "KafkaMessage",
    "KafkaProducer",
    "KafkaProducerError",
    "KafkaRecord",
    "ServiceClient",
    "create_kafka_consumer",
    "create_http_client",
    "create_kafka_producer",
]
