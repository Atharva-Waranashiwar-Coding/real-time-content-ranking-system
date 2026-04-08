# Local Monitoring Runbook

## Goal

Bring up Prometheus and Grafana locally, run the application services on the host, and verify that metrics and dashboards are populated.

## Start Infrastructure

1. Start the monitoring stack and core infra:

```bash
docker compose -f infra/docker/docker-compose.yml up -d postgres redis zookeeper kafka prometheus grafana
```

2. Start the application services on the host on ports `8000` through `8008`.

Prometheus is configured to scrape `host.docker.internal:<port>` so the services should run on the host network, not inside the same Docker Compose file.

## Verify Scraping

1. Open Prometheus at `http://localhost:9090/targets`.
2. Confirm each job is `UP`.
3. Run a few direct checks:

```bash
curl -s http://localhost:8004/metrics | rg content_ranking_feed_assembly_duration_seconds
curl -s http://localhost:8005/metrics | rg content_ranking_ranking_duration_seconds
curl -s http://localhost:8008/metrics | rg content_ranking_consumer_lag
```

## Open Grafana

1. Open `http://localhost:3000`.
2. Log in with the credentials from `.env` or `.env.example`.
3. Navigate to the `Content Ranking` folder.

Provisioned dashboards:

- `Platform Overview`
- `Event Pipeline`
- `Ranking and Feed Operations`

## Readiness and Liveness

Useful health checks:

```bash
curl -s http://localhost:8004/api/v1/live
curl -s http://localhost:8004/api/v1/ready
curl -s http://localhost:8008/api/v1/ready
```

Expected patterns:

- `/api/v1/live`: process is up
- `/api/v1/ready`: critical dependencies are reachable where the service has direct dependencies

## Recommended Demo Flow

1. Load the web demo and request a few feeds.
2. Trigger `click`, `like`, `save`, and `skip` interactions.
3. Watch `Event Pipeline` for publish/consume activity.
4. Inspect `Ranking and Feed Operations` for ranking/feed latency movement.
