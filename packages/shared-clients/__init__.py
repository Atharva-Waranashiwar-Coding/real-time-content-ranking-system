"""Shared HTTP and Kafka client utilities for the ranking platform."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, Protocol

import httpx

from shared_config import settings as base_settings
from shared_logging import observe_dependency_request, record_retry_attempt

RETRYABLE_HTTP_STATUS_CODES = frozenset({429, 500, 502, 503, 504})


@dataclass(frozen=True)
class RetryPolicy:
    """Retry policy for external dependencies."""

    max_attempts: int = 1
    initial_delay_seconds: float = 0.0
    max_delay_seconds: float = 0.0
    backoff_multiplier: float = 2.0

    def next_delay(self, current_delay: float) -> float:
        """Return the next bounded delay value."""

        if current_delay <= 0:
            current_delay = self.initial_delay_seconds
        if current_delay <= 0:
            return 0.0
        return min(current_delay * self.backoff_multiplier, self.max_delay_seconds)


DEFAULT_HTTP_RETRY_POLICY = RetryPolicy(
    max_attempts=base_settings.HTTP_CLIENT_RETRY_MAX_ATTEMPTS,
    initial_delay_seconds=base_settings.HTTP_CLIENT_RETRY_INITIAL_DELAY_SECONDS,
    max_delay_seconds=base_settings.HTTP_CLIENT_RETRY_MAX_DELAY_SECONDS,
    backoff_multiplier=base_settings.HTTP_CLIENT_RETRY_BACKOFF_MULTIPLIER,
)
DEFAULT_KAFKA_RETRY_POLICY = RetryPolicy(
    max_attempts=base_settings.KAFKA_PUBLISH_RETRY_MAX_ATTEMPTS,
    initial_delay_seconds=base_settings.KAFKA_PUBLISH_RETRY_INITIAL_DELAY_SECONDS,
    max_delay_seconds=base_settings.KAFKA_PUBLISH_RETRY_MAX_DELAY_SECONDS,
    backoff_multiplier=base_settings.KAFKA_PUBLISH_RETRY_BACKOFF_MULTIPLIER,
)


async def create_http_client(timeout: float = 10.0) -> httpx.AsyncClient:
    """Create an async HTTP client."""

    return httpx.AsyncClient(timeout=timeout)


class ServiceClient:
    """Base client for inter-service HTTP communication."""

    def __init__(
        self,
        base_url: str,
        timeout: float = 10.0,
        *,
        caller_service: str | None = None,
        dependency_name: str | None = None,
        retry_policy: RetryPolicy | None = None,
    ):
        """Initialize a service client."""

        self.base_url = base_url
        self.timeout = timeout
        self.caller_service = caller_service
        self.dependency_name = dependency_name
        self.retry_policy = retry_policy or DEFAULT_HTTP_RETRY_POLICY
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

        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs: Any) -> httpx.Response:
        """Make a POST request."""

        return await self.request("POST", path, **kwargs)

    async def request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        """Make an outbound HTTP request with retry/backoff instrumentation."""

        if not self.client:
            raise RuntimeError("Client not initialized. Use async context manager.")

        delay_seconds = self.retry_policy.initial_delay_seconds
        operation = method.upper()
        for attempt in range(1, self.retry_policy.max_attempts + 1):
            started_at = perf_counter()
            try:
                response = await self.client.request(
                    operation,
                    f"{self.base_url}{path}",
                    **kwargs,
                )
            except httpx.TransportError:
                duration_seconds = perf_counter() - started_at
                self._record_dependency(
                    operation=operation,
                    duration_seconds=duration_seconds,
                    outcome="transport_error",
                )
                if attempt >= self.retry_policy.max_attempts:
                    raise
                self._record_retry(operation)
                await asyncio.sleep(delay_seconds)
                delay_seconds = self.retry_policy.next_delay(delay_seconds)
                continue

            duration_seconds = perf_counter() - started_at
            outcome = (
                "success"
                if response.status_code not in RETRYABLE_HTTP_STATUS_CODES
                else f"status_{response.status_code}"
            )
            self._record_dependency(
                operation=operation,
                duration_seconds=duration_seconds,
                outcome=outcome,
            )
            if (
                response.status_code in RETRYABLE_HTTP_STATUS_CODES
                and attempt < self.retry_policy.max_attempts
            ):
                self._record_retry(operation)
                await asyncio.sleep(delay_seconds)
                delay_seconds = self.retry_policy.next_delay(delay_seconds)
                continue
            return response

        raise RuntimeError("HTTP request retry loop exited unexpectedly")

    def _record_dependency(
        self,
        *,
        operation: str,
        duration_seconds: float,
        outcome: str,
    ) -> None:
        """Record outbound dependency metrics when caller metadata is available."""

        if self.caller_service is None or self.dependency_name is None:
            return
        observe_dependency_request(
            service_name=self.caller_service,
            dependency_name=self.dependency_name,
            operation=operation,
            outcome=outcome,
            duration_seconds=duration_seconds,
        )

    def _record_retry(self, operation: str) -> None:
        """Record retry attempts when caller metadata is available."""

        if self.caller_service is None or self.dependency_name is None:
            return
        record_retry_attempt(
            service_name=self.caller_service,
            dependency_name=self.dependency_name,
            operation=operation,
        )


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


@dataclass(frozen=True)
class KafkaLagSnapshot:
    """Kafka consumer lag snapshot for a single partition."""

    group_id: str
    topic: str
    partition: int
    current_offset: int
    end_offset: int
    lag: int


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

    async def lag_snapshots(self) -> list[KafkaLagSnapshot]:
        """Return lag snapshots for the consumer's assigned partitions."""

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
        retry_policy: RetryPolicy | None = None,
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
        self._client_id = client_id
        self._flush_timeout_seconds = flush_timeout_seconds
        self._retry_policy = retry_policy or DEFAULT_KAFKA_RETRY_POLICY

    async def publish(self, message: KafkaMessage) -> None:
        """Publish a message and wait for delivery confirmation."""

        delay_seconds = self._retry_policy.initial_delay_seconds
        for attempt in range(1, self._retry_policy.max_attempts + 1):
            started_at = perf_counter()
            try:
                await asyncio.to_thread(self._publish_sync, message)
            except KafkaProducerError:
                duration_seconds = perf_counter() - started_at
                observe_dependency_request(
                    service_name=self._client_id,
                    dependency_name="kafka",
                    operation="PUBLISH",
                    outcome="error",
                    duration_seconds=duration_seconds,
                )
                if attempt >= self._retry_policy.max_attempts:
                    raise
                record_retry_attempt(
                    service_name=self._client_id,
                    dependency_name="kafka",
                    operation="PUBLISH",
                )
                await asyncio.sleep(delay_seconds)
                delay_seconds = self._retry_policy.next_delay(delay_seconds)
                continue

            observe_dependency_request(
                service_name=self._client_id,
                dependency_name="kafka",
                operation="PUBLISH",
                outcome="success",
                duration_seconds=perf_counter() - started_at,
            )
            return

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
        self._group_id = group_id
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

    async def lag_snapshots(self) -> list[KafkaLagSnapshot]:
        """Return current lag information for assigned partitions."""

        return await asyncio.to_thread(self._lag_snapshots_sync)

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

    def _lag_snapshots_sync(self) -> list[KafkaLagSnapshot]:
        """Fetch lag snapshots for assigned partitions."""

        assignments = self._consumer.assignment()
        if not assignments:
            return []

        positions = self._consumer.position(assignments)
        snapshots: list[KafkaLagSnapshot] = []
        for topic_partition in positions:
            low_offset, high_offset = self._consumer.get_watermark_offsets(
                topic_partition,
                timeout=1.0,
                cached=False,
            )
            current_offset = (
                topic_partition.offset
                if topic_partition.offset is not None and topic_partition.offset >= 0
                else low_offset
            )
            snapshots.append(
                KafkaLagSnapshot(
                    group_id=self._group_id,
                    topic=topic_partition.topic,
                    partition=topic_partition.partition,
                    current_offset=current_offset,
                    end_offset=high_offset,
                    lag=max(high_offset - current_offset, 0),
                )
            )
        return snapshots


def create_kafka_producer(
    bootstrap_servers: str,
    client_id: str,
    extra_config: dict[str, Any] | None = None,
) -> KafkaProducer:
    """Create the default Kafka producer implementation."""

    return ConfluentKafkaProducer(
        bootstrap_servers=bootstrap_servers,
        client_id=client_id,
        retry_policy=DEFAULT_KAFKA_RETRY_POLICY,
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
    "KafkaLagSnapshot",
    "KafkaMessage",
    "KafkaProducer",
    "KafkaProducerError",
    "KafkaRecord",
    "RetryPolicy",
    "ServiceClient",
    "create_kafka_consumer",
    "create_http_client",
    "create_kafka_producer",
]
