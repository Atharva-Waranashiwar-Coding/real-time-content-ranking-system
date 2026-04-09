#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/infra/docker/docker-compose.yml"
RUNTIME_DIR="${TMPDIR:-/tmp}/content-ranking-system-local-stack"
PID_DIR="${RUNTIME_DIR}/pids"
LOG_DIR="${RUNTIME_DIR}/logs"

readonly ROOT_DIR
readonly COMPOSE_FILE
readonly RUNTIME_DIR
readonly PID_DIR
readonly LOG_DIR

SERVICES=(
  "api-gateway:8000"
  "user-service:8001"
  "content-service:8002"
  "interaction-service:8003"
  "ranking-service:8005"
  "feed-service:8004"
  "experimentation-service:8006"
  "analytics-service:8007"
  "feature-processor:8008"
)

usage() {
  cat <<'EOF'
Usage:
  bash scripts/run_platform_stack.sh
  bash scripts/run_platform_stack.sh up
  bash scripts/run_platform_stack.sh down
  bash scripts/run_platform_stack.sh status

Commands:
  up      Start infra, run migrations, reseed reference data, start all services, build and start the frontend
  down    Stop all managed app processes and docker compose infrastructure
  status  Show process and health status for the managed stack
EOF
}

log() {
  printf '[stack] %s\n' "$1"
}

fail() {
  printf '[stack] ERROR: %s\n' "$1" >&2
  exit 1
}

require_command() {
  local command_name="$1"
  command -v "${command_name}" >/dev/null 2>&1 || fail "Required command not found: ${command_name}"
}

ensure_runtime_dirs() {
  mkdir -p "${PID_DIR}" "${LOG_DIR}"
}

ensure_env_files() {
  if [[ ! -f "${ROOT_DIR}/.env" ]]; then
    cp "${ROOT_DIR}/.env.example" "${ROOT_DIR}/.env"
    log "Created .env from .env.example"
  fi

  if [[ ! -f "${ROOT_DIR}/apps/web/.env.local" ]]; then
    cp "${ROOT_DIR}/apps/web/.env.example" "${ROOT_DIR}/apps/web/.env.local"
    log "Created apps/web/.env.local from apps/web/.env.example"
  fi
}

resolve_python_bin() {
  if [[ -n "${VIRTUAL_ENV:-}" && -x "${VIRTUAL_ENV}/bin/python" ]]; then
    printf '%s\n' "${VIRTUAL_ENV}/bin/python"
    return
  fi

  if [[ -x "${ROOT_DIR}/.venv/bin/python" ]]; then
    printf '%s\n' "${ROOT_DIR}/.venv/bin/python"
    return
  fi

  fail "No project virtualenv found. Create .venv first and install the Python dependencies."
}

pid_file_for() {
  local process_name="$1"
  printf '%s/%s.pid\n' "${PID_DIR}" "${process_name}"
}

is_pid_running() {
  local process_id="$1"
  kill -0 "${process_id}" >/dev/null 2>&1
}

read_pid() {
  local process_name="$1"
  local pid_file
  pid_file="$(pid_file_for "${process_name}")"
  if [[ -f "${pid_file}" ]]; then
    cat "${pid_file}"
  fi
}

cleanup_stale_pid_file() {
  local process_name="$1"
  local pid_file
  pid_file="$(pid_file_for "${process_name}")"
  if [[ -f "${pid_file}" ]]; then
    local process_id
    process_id="$(cat "${pid_file}")"
    if ! is_pid_running "${process_id}"; then
      rm -f "${pid_file}"
    fi
  fi
}

port_listener_pid() {
  local port="$1"
  if ! command -v lsof >/dev/null 2>&1; then
    return 0
  fi
  lsof -tiTCP:"${port}" -sTCP:LISTEN 2>/dev/null | head -n 1 || true
}

ensure_port_is_available() {
  local process_name="$1"
  local port="$2"

  cleanup_stale_pid_file "${process_name}"

  local listener_pid managed_pid
  listener_pid="$(port_listener_pid "${port}")"
  managed_pid="$(read_pid "${process_name}" || true)"

  if [[ -n "${listener_pid}" ]]; then
    if [[ -n "${managed_pid}" && "${listener_pid}" == "${managed_pid}" ]]; then
      return
    fi
    fail "Port ${port} is already in use by another process (${listener_pid}). Stop it before starting ${process_name}."
  fi
}

wait_for_tcp() {
  local host="$1"
  local port="$2"
  local label="$3"
  local timeout_seconds="${4:-60}"

  for ((attempt = 1; attempt <= timeout_seconds; attempt += 1)); do
    if (echo >/dev/tcp/"${host}"/"${port}") >/dev/null 2>&1; then
      log "${label} is ready on ${host}:${port}"
      return
    fi
    sleep 1
  done

  fail "Timed out waiting for ${label} on ${host}:${port}"
}

wait_for_http() {
  local url="$1"
  local label="$2"
  local timeout_seconds="${3:-90}"

  for ((attempt = 1; attempt <= timeout_seconds; attempt += 1)); do
    if curl -fsS "${url}" >/dev/null 2>&1; then
      log "${label} is healthy at ${url}"
      return
    fi
    sleep 1
  done

  fail "Timed out waiting for ${label} at ${url}. Check ${LOG_DIR}/${label}.log"
}

stop_managed_process() {
  local process_name="$1"
  local pid_file process_id
  pid_file="$(pid_file_for "${process_name}")"

  if [[ ! -f "${pid_file}" ]]; then
    return
  fi

  process_id="$(cat "${pid_file}")"
  if ! is_pid_running "${process_id}"; then
    rm -f "${pid_file}"
    return
  fi

  log "Stopping ${process_name} (${process_id})"
  kill "${process_id}" >/dev/null 2>&1 || true
  for _ in {1..20}; do
    if ! is_pid_running "${process_id}"; then
      rm -f "${pid_file}"
      return
    fi
    sleep 1
  done

  kill -9 "${process_id}" >/dev/null 2>&1 || true
  rm -f "${pid_file}"
}

stop_managed_apps() {
  stop_managed_process "web"

  local entry process_name
  for entry in "${SERVICES[@]}"; do
    process_name="${entry%%:*}"
    stop_managed_process "${process_name}"
  done
}

start_backend_service() {
  local process_name="$1"
  local port="$2"
  local python_bin="$3"
  local pid_file log_file

  ensure_port_is_available "${process_name}" "${port}"

  pid_file="$(pid_file_for "${process_name}")"
  log_file="${LOG_DIR}/${process_name}.log"

  log "Starting ${process_name} on port ${port}"
  (
    cd "${ROOT_DIR}"
    export PYTHONPATH="${ROOT_DIR}"
    export PYTHONUNBUFFERED=1
    nohup "${python_bin}" -m uvicorn app.main:app \
      --app-dir "${ROOT_DIR}/services/${process_name}" \
      --host 0.0.0.0 \
      --port "${port}" \
      >"${log_file}" 2>&1 &
    echo $! >"${pid_file}"
  )

  wait_for_http "http://localhost:${port}/api/v1/health" "${process_name}"
}

ensure_frontend_dependencies() {
  if [[ ! -d "${ROOT_DIR}/apps/web/node_modules" ]]; then
    log "Installing frontend dependencies"
    npm --prefix "${ROOT_DIR}/apps/web" install
  fi
}

start_frontend() {
  local pid_file log_file build_log

  ensure_port_is_available "web" "3001"
  ensure_frontend_dependencies

  build_log="${LOG_DIR}/web-build.log"
  log "Building frontend"
  npm --prefix "${ROOT_DIR}/apps/web" run build >"${build_log}" 2>&1

  pid_file="$(pid_file_for "web")"
  log_file="${LOG_DIR}/web.log"
  log "Starting frontend on port 3001"
  (
    cd "${ROOT_DIR}"
    nohup npm --prefix "${ROOT_DIR}/apps/web" run start -- -H 0.0.0.0 -p 3001 \
      >"${log_file}" 2>&1 &
    echo $! >"${pid_file}"
  )

  wait_for_http "http://localhost:3001" "web"
}

bootstrap_stack() {
  local python_bin
  python_bin="$(resolve_python_bin)"

  require_command docker
  require_command npm
  require_command curl
  ensure_runtime_dirs
  ensure_env_files

  stop_managed_apps

  log "Starting infrastructure"
  docker compose -f "${COMPOSE_FILE}" up -d

  wait_for_tcp "localhost" "5432" "PostgreSQL"
  wait_for_tcp "localhost" "6379" "Redis"
  wait_for_tcp "localhost" "9092" "Kafka"

  log "Running database migrations"
  bash "${ROOT_DIR}/scripts/run_migrations.sh"

  log "Bootstrapping reference data"
  bash "${ROOT_DIR}/scripts/setup_demo.sh"

  start_backend_service "api-gateway" "8000" "${python_bin}"
  start_backend_service "user-service" "8001" "${python_bin}"
  start_backend_service "content-service" "8002" "${python_bin}"
  start_backend_service "interaction-service" "8003" "${python_bin}"
  start_backend_service "ranking-service" "8005" "${python_bin}"
  start_backend_service "experimentation-service" "8006" "${python_bin}"
  start_backend_service "analytics-service" "8007" "${python_bin}"
  start_backend_service "feature-processor" "8008" "${python_bin}"
  start_backend_service "feed-service" "8004" "${python_bin}"

  start_frontend

  cat <<EOF

[stack] Platform stack is ready
[stack] Frontend:              http://localhost:3001
[stack] API Gateway:           http://localhost:8000/api/v1/health
[stack] User Service:          http://localhost:8001/api/v1/health
[stack] Content Service:       http://localhost:8002/api/v1/health
[stack] Interaction Service:   http://localhost:8003/api/v1/health
[stack] Feed Service:          http://localhost:8004/api/v1/health
[stack] Ranking Service:       http://localhost:8005/api/v1/health
[stack] Experimentation:       http://localhost:8006/api/v1/health
[stack] Analytics Service:     http://localhost:8007/api/v1/health
[stack] Feature Processor:     http://localhost:8008/api/v1/health
[stack] Prometheus:            http://localhost:9090
[stack] Grafana:               http://localhost:3000
[stack] Logs:                  ${LOG_DIR}

To stop everything:
  bash scripts/run_platform_stack.sh down
EOF
}

shutdown_stack() {
  require_command docker
  ensure_runtime_dirs

  stop_managed_apps
  log "Stopping infrastructure"
  docker compose -f "${COMPOSE_FILE}" down
}

stack_status() {
  ensure_runtime_dirs

  printf 'Managed process status\n'
  printf '======================\n'

  local entry process_name port process_id health_url health_status
  for entry in "web:3001" "${SERVICES[@]}"; do
    process_name="${entry%%:*}"
    port="${entry##*:}"
    cleanup_stale_pid_file "${process_name}"
    process_id="$(read_pid "${process_name}" || true)"
    health_url="http://localhost:${port}"
    if [[ "${process_name}" != "web" ]]; then
      health_url="${health_url}/api/v1/health"
    fi

    if curl -fsS "${health_url}" >/dev/null 2>&1; then
      health_status="healthy"
    else
      health_status="down"
    fi

    printf '%-24s pid=%-8s port=%-5s health=%s\n' \
      "${process_name}" \
      "${process_id:-"-"}" \
      "${port}" \
      "${health_status}"
  done

  printf '\nLogs directory: %s\n' "${LOG_DIR}"
}

main() {
  local command="${1:-up}"

  case "${command}" in
    up)
      bootstrap_stack
      ;;
    down)
      shutdown_stack
      ;;
    status)
      stack_status
      ;;
    help|-h|--help)
      usage
      ;;
    *)
      usage
      exit 1
      ;;
  esac
}

main "${1:-up}"
