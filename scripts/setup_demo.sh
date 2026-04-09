#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

echo "[demo] Resetting canonical demo state"
python scripts/reset_demo_state.py

echo "[demo] Seeding canonical users"
python scripts/seed_users.py

echo "[demo] Seeding canonical content"
python scripts/seed_content.py

echo "[demo] Seeding deterministic features and experiment analytics"
python scripts/seed_demo_state.py

echo "[demo] Demo bootstrap complete"
