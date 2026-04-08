# Debugging Runbook

## Missing Metrics

Symptoms:

- Prometheus target is `DOWN`
- Grafana panels show `No data`

Checks:

1. Verify the service is running locally on the expected port.
2. Check the scrape target page in Prometheus.
3. Curl the metrics endpoint directly:

```bash
curl -s http://localhost:8003/metrics | head
```

4. Confirm the monitoring container can reach the host:

```bash
docker exec ranking_prometheus wget -qO- http://host.docker.internal:8003/metrics | head
```

## Rising Feed or Ranking Latency

Signals:

- `content_ranking_feed_assembly_duration_seconds`
- `content_ranking_ranking_duration_seconds`
- `content_ranking_dependency_request_duration_seconds`
- `content_ranking_retry_attempts_total`

Debug path:

1. Check whether latency is isolated to cache misses in the feed dashboard.
2. Look for spikes in retries from feed-service to ranking-service or experimentation-service.
3. Search logs by `correlation_id` to trace the slow request across services.

## Feature Processor Backlog

Signals:

- `content_ranking_consumer_lag`
- `feature_processor_events_failed_total`
- `content_ranking_event_operations_total{service="feature-processor",operation="dlq_publish"}`

Debug path:

1. If lag rises while failures stay flat, the processor is simply behind; inspect CPU and traffic volume.
2. If lag rises with failures, inspect dead-letter events and processor logs.
3. Check the dead-letter topic:

```bash
docker exec ranking_kafka kafka-console-consumer.sh \
  --bootstrap-server kafka:9092 \
  --topic interactions.events.dlq.v1 \
  --from-beginning
```

## DLQ Investigation

Each `dead_letter_event.v1` record includes:

- source topic, partition, and offset
- original Kafka headers
- failed service name
- error type and message
- request and correlation IDs
- original payload

Use that payload to determine whether the issue was:

- invalid schema or bad producer payload
- transient downstream failure that exhausted retries
- a deterministic processor bug

## Structured Log Search

The minimum fields to search:

- `request_id`
- `correlation_id`
- `event_id`
- `decision_id`
- `kafka_topic`

Typical path:

1. Start from the HTTP ingress log in feed-service or interaction-service.
2. Follow the same `correlation_id` into ranking-service or feature-processor logs.
3. If the event was dead-lettered, match the same IDs in the DLQ payload.
