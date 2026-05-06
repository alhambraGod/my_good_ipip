#!/usr/bin/env bash
# Horizontally scale frontend/backend replicas of a running compose stack.
#
# Usage:
#   bash deploy/scale.sh dev backend=2 frontend=2
#   bash deploy/scale.sh prod backend=3
#
# Compose's built-in DNS round-robins service names, so nginx upstreams
# don't need to change for in-host scale-out.

set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
# shellcheck disable=SC1091
source "$HERE/_lib.sh"

ENV="${1:-dev}"; shift || die "Usage: $0 <dev|prod> backend=N [frontend=N]…"
COMPOSE_FILE="$(pick_compose_file "$ENV")"
SCALE_ARGS=("$@")

require_cmd docker
[[ ${#SCALE_ARGS[@]} -gt 0 ]] || die "Pass at least one service=N pair"

log_section "MindPrism — scale.sh ($ENV) → ${SCALE_ARGS[*]}"
cd "$ROOT"

flags=()
for pair in "${SCALE_ARGS[@]}"; do
  flags+=(--scale "$pair")
done
docker compose -f "$COMPOSE_FILE" up -d "${flags[@]}"

log_ok "Scaled. Run \`docker compose -f $COMPOSE_FILE ps\` to confirm."
log_info "Note: nginx upstreams resolve service names dynamically; no nginx reload needed."
