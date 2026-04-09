# Scripts

This directory contains the local developer utilities used to run, reset, and demo the system.

## Most Important Commands

### Bootstrap a deterministic demo

```bash
bash scripts/setup_demo.sh
```

This sequence:

- removes canonical demo records and Redis keys
- seeds the 5 demo users and 50+ content items
- seeds deterministic Redis feature vectors
- seeds experiment assignments, exposures, and attributed interaction outcomes

For a fully frozen walkthrough:

```bash
export DEMO_REFERENCE_TIME=2026-04-08T14:00:00+00:00
export RANKING_FIXED_NOW=2026-04-08T14:00:00+00:00
bash scripts/setup_demo.sh
```

### Reset demo state only

```bash
python scripts/reset_demo_state.py
```

### Seed canonical users and content only

```bash
python scripts/seed_users.py
python scripts/seed_content.py
```

### Seed deterministic feature and experiment state only

```bash
python scripts/seed_demo_state.py
```

### Run a backend service from source

```bash
bash scripts/run_service.sh user-service
bash scripts/run_service.sh feed-service
```

This helper sets the repository root on `PYTHONPATH`, loads repo-local shared packages, and starts `uvicorn` with the correct service directory and default port.

### Run all required Alembic migrations

```bash
bash scripts/run_migrations.sh
```

This helper prefers the active virtualenv's `alembic` binary, then falls back to `.venv/bin/alembic` if present.

## Other Utilities

- `format.sh`: repository formatting helper
- `lint.sh`: repository lint helper

## Data Contract Notes

The deterministic demo data is defined in `demo_dataset.py`.

Key guarantees:

- demo users have fixed UUIDs
- demo content and tags have fixed UUIDs
- experiment buckets are deterministic
- seeded Redis features line up with the published content catalog
- the experiment dashboard is non-empty immediately after bootstrap
