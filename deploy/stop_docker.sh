#!/usr/bin/env bash
# Stop the MindPrism docker stack.
# Usage: bash deploy/stop_docker.sh [dev|prod] [--volumes]

set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
# shellcheck disable=SC1091
source "$HERE/_lib.sh"

ENV="${1:-dev}"; shift || true
EXTRA_ARGS=("$@")
COMPOSE_FILE="$(pick_compose_file "$ENV")"

require_cmd docker

log_section "MindPrism — stop_docker.sh ($ENV)"
cd "$ROOT"

if [[ " ${EXTRA_ARGS[*]} " == *" --volumes "* ]]; then
  log_warn "Stopping AND removing volumes (data will be lost!)"
  docker compose -f "$COMPOSE_FILE" down --volumes --remove-orphans
else
  docker compose -f "$COMPOSE_FILE" down --remove-orphans
fi
log_ok "Stopped."
