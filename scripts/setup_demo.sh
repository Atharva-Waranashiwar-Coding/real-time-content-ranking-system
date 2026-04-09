#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

resolve_python_bin() {
  if [[ -n "${VIRTUAL_ENV:-}" && -x "${VIRTUAL_ENV}/bin/python" ]]; then
    printf '%s\n' "${VIRTUAL_ENV}/bin/python"
    return
  fi

  if [[ -x "${ROOT_DIR}/.venv/bin/python" ]]; then
    printf '%s\n' "${ROOT_DIR}/.venv/bin/python"
    return
  fi

  if command -v python >/dev/null 2>&1; then
    command -v python
    return
  fi

  echo "Unable to find a Python executable. Create .venv first and install the project dependencies." >&2
  exit 1
}

PYTHON_BIN="$(resolve_python_bin)"

echo "[setup] Resetting reference dataset"
"${PYTHON_BIN}" scripts/reset_demo_state.py

echo "[setup] Seeding reference users"
"${PYTHON_BIN}" scripts/seed_users.py

echo "[setup] Seeding reference content"
"${PYTHON_BIN}" scripts/seed_content.py

echo "[setup] Seeding deterministic ranking features and experiment analytics"
"${PYTHON_BIN}" scripts/seed_demo_state.py

echo "[setup] Reference dataset bootstrap complete"
