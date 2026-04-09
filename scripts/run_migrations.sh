#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

resolve_alembic_bin() {
  if [[ -n "${VIRTUAL_ENV:-}" && -x "${VIRTUAL_ENV}/bin/alembic" ]]; then
    printf '%s\n' "${VIRTUAL_ENV}/bin/alembic"
    return
  fi

  if [[ -x "${ROOT_DIR}/.venv/bin/alembic" ]]; then
    printf '%s\n' "${ROOT_DIR}/.venv/bin/alembic"
    return
  fi

  if command -v alembic >/dev/null 2>&1; then
    command -v alembic
    return
  fi

  echo "Unable to find an alembic executable. Install service dependencies into a virtualenv first." >&2
  exit 1
}

ALEMBIC_BIN="$(resolve_alembic_bin)"
SERVICES=(
  "user-service"
  "content-service"
  "interaction-service"
  "experimentation-service"
  "feature-processor"
)

for service in "${SERVICES[@]}"; do
  echo "[migrations] ${service}"
  (
    cd "${ROOT_DIR}/services/${service}"
    PYTHONPATH=../.. "${ALEMBIC_BIN}" upgrade head
  )
done
