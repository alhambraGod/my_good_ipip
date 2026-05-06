#!/usr/bin/env bash
# Start MindPrism via Docker Compose.
#
# Usage:
#   bash deploy/start_docker.sh dev          # bring up dev stack (incl. mysql)
#   bash deploy/start_docker.sh prod         # bring up prod stack (host mysql)
#   bash deploy/start_docker.sh dev --build  # force image rebuild
#   bash deploy/start_docker.sh dev --pull   # pull updated base images first

set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
# shellcheck disable=SC1091
source "$HERE/_lib.sh"

ENV="${1:-dev}"; shift || true
EXTRA_ARGS=("$@")
COMPOSE_FILE="$(pick_compose_file "$ENV")"

require_cmd docker
require_cmd docker  # we'll call `docker compose` (v2)

log_section "MindPrism — start_docker.sh ($ENV)"

ensure_log_dirs "$ENV"
load_env_file "$ENV" "$ROOT"

cd "$ROOT"
log_info "Compose file: $COMPOSE_FILE"
log_info "Network:      mindprism-${ENV}"

# Pull / build first so a fresh user gets a deterministic state.
if [[ " ${EXTRA_ARGS[*]} " == *" --pull "* ]]; then
  log_info "Pulling base images…"
  docker compose -f "$COMPOSE_FILE" pull
fi

log_info "Building images…"
if [[ " ${EXTRA_ARGS[*]} " == *" --build "* ]]; then
  docker compose -f "$COMPOSE_FILE" build --no-cache
else
  docker compose -f "$COMPOSE_FILE" build
fi

log_info "Bringing services up (detached)…"
docker compose -f "$COMPOSE_FILE" up -d

log_info "Waiting for nginx to report healthy…"
for i in {1..30}; do
  status="$(docker compose -f "$COMPOSE_FILE" ps --status running --services | wc -l | tr -d ' ')"
  if [[ "$status" -ge "3" ]]; then break; fi
  sleep 1
done

log_section "Service status"
docker compose -f "$COMPOSE_FILE" ps

log_section "Tail one line each (last 20 lines)"
docker compose -f "$COMPOSE_FILE" logs --tail=20

log_ok  "MindPrism ($ENV) is up."
log_info "Frontend (via nginx):    http://localhost"
log_info "Backend  (direct):       http://127.0.0.1:3001"
log_info "Logs:                    /var/MindPrism/${ENV}/logs/"
log_info "Stop:                    bash deploy/stop_docker.sh $ENV"
