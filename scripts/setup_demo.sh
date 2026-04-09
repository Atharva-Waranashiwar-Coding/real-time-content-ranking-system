#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

echo "[setup] Resetting reference dataset"
python scripts/reset_demo_state.py

echo "[setup] Seeding reference users"
python scripts/seed_users.py

echo "[setup] Seeding reference content"
python scripts/seed_content.py

echo "[setup] Seeding deterministic ranking features and experiment analytics"
python scripts/seed_demo_state.py

echo "[setup] Reference dataset bootstrap complete"
