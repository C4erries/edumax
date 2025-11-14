#!/usr/bin/env bash
set -euo pipefail

COMPOSE_CMD="${COMPOSE_CMD:-docker compose}"
BACKEND_HEALTH_URL="${BACKEND_HEALTH_URL:-http://localhost:8000/health}"
BOT_HEALTH_URL="${BOT_HEALTH_URL:-http://localhost:8080/healthz}"

info() {
  printf '==> %s\n' "$*"
}

warn() {
  printf '[warn] %s\n' "$*" >&2
}

wait_for() {
  local url=$1
  local name=$2
  info "Waiting for ${name} at ${url}"
  until curl -fsS "$url" >/dev/null 2>&1; do
    sleep 1
  done
}

if [[ "${WITH_REBUILD:-0}" == "1" ]]; then
  info "Rebuilding backend and bot images"
  $COMPOSE_CMD build backend bot
else
  warn "Skipping image rebuild (WITH_REBUILD=0)"
fi

info "Starting backend and bot containers (detached)"
$COMPOSE_CMD up -d backend bot

wait_for "$BACKEND_HEALTH_URL" "backend"
wait_for "$BOT_HEALTH_URL" "bot"

if [[ "${SKIP_SEED:-0}" != "1" ]]; then
  info "Seeding database inside backend container (init_db.sh)"
  $COMPOSE_CMD exec backend bash -lc "bash ./init_db.sh"
else
  info "Skipping database seed because SKIP_SEED=${SKIP_SEED}"
fi

info "Backend health response:"
curl -fsS "$BACKEND_HEALTH_URL"
printf '\n'

info "Bot health response:"
curl -fsS "$BOT_HEALTH_URL"
printf '\n'

info "Container status:"
$COMPOSE_CMD ps backend bot
