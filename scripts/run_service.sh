#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_NAME="${1:-}"

if [[ -z "${SERVICE_NAME}" ]]; then
  echo "Usage: bash scripts/run_service.sh <service-name> [uvicorn args...]" >&2
  exit 1
fi

case "${SERVICE_NAME}" in
  api-gateway) SERVICE_PORT=8000 ;;
  user-service) SERVICE_PORT=8001 ;;
  content-service) SERVICE_PORT=8002 ;;
  interaction-service) SERVICE_PORT=8003 ;;
  feed-service) SERVICE_PORT=8004 ;;
  ranking-service) SERVICE_PORT=8005 ;;
  experimentation-service) SERVICE_PORT=8006 ;;
  analytics-service) SERVICE_PORT=8007 ;;
  feature-processor) SERVICE_PORT=8008 ;;
  *)
    echo "Unknown service: ${SERVICE_NAME}" >&2
    exit 1
    ;;
esac

shift
export PYTHONPATH="${ROOT_DIR}${PYTHONPATH:+:${PYTHONPATH}}"

exec python -m uvicorn app.main:app \
  --app-dir "${ROOT_DIR}/services/${SERVICE_NAME}" \
  --host 0.0.0.0 \
  --port "${SERVICE_PORT}" \
  --reload \
  "$@"
