#!/usr/bin/env bash
# Native (no-Docker) start. Intended for laptops + small VMs that have:
#   - Python 3.11 (via conda or pyenv)
#   - Node 20+
#   - (prod only) MySQL 8.x running on the host
#
# Usage:
#   bash deploy/start_native.sh dev       # SQLite by default if MySQL missing
#   bash deploy/start_native.sh prod      # requires DATABASE_URL pointing at host MySQL

set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
# shellcheck disable=SC1091
source "$HERE/_lib.sh"

ENV="${1:-dev}"
[[ "$ENV" == "dev" || "$ENV" == "prod" ]] || die "Usage: $0 <dev|prod>"

log_section "MindPrism — start_native.sh ($ENV)"

ensure_log_dirs "$ENV"
load_env_file "$ENV" "$ROOT"

# ── Backend ────────────────────────────────────────────────────────────
log_info "[1/2] Backend"
cd "$ROOT/backend"

# Conda fast-path; otherwise rely on whatever python3.11 is in PATH.
if command -v conda >/dev/null 2>&1; then
  CONDA_BASE="$(conda info --base 2>/dev/null || true)"
  if [[ -n "$CONDA_BASE" && -f "$CONDA_BASE/etc/profile.d/conda.sh" ]]; then
    # shellcheck disable=SC1091
    source "$CONDA_BASE/etc/profile.d/conda.sh"
    if conda info --envs | grep -q "^my_good_ipip "; then
      conda activate my_good_ipip
    fi
  fi
fi

require_cmd python3
require_cmd uvicorn || pip install -r requirements.txt
pip install -q -r requirements.txt

# Generate backend/.env from central env file if available.
if [[ -f "$ROOT/env/${ENV}.env" ]]; then
  grep -v '^#' "$ROOT/env/${ENV}.env" | grep -v '^NEXT_PUBLIC_' | grep -v '^$' \
    > "$ROOT/backend/.env"
  log_ok "Generated backend/.env"
fi

# Start backend; logs are routed by setup_logging() to /var/MindPrism/$ENV/logs.
if [[ "$ENV" == "dev" ]]; then
  log_info "Starting uvicorn (--reload)…"
  uvicorn main:app --host 0.0.0.0 --port 3001 --reload &
  BACKEND_PID=$!
else
  WORKERS="${GUNICORN_WORKERS:-2}"
  log_info "Starting gunicorn ($WORKERS workers)…"
  gunicorn main:app --bind 0.0.0.0:3001 \
    --workers "$WORKERS" \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 60 --keep-alive 5 --access-logfile - --error-logfile - &
  BACKEND_PID=$!
fi

# ── Frontend ───────────────────────────────────────────────────────────
log_info "[2/2] Frontend"
cd "$ROOT/frontend"

if [[ -f "$ROOT/env/${ENV}.env" ]]; then
  grep '^NEXT_PUBLIC_' "$ROOT/env/${ENV}.env" > "$ROOT/frontend/.env.local" || true
  log_ok "Generated frontend/.env.local"
fi

require_cmd npm
npm install --silent

if [[ "$ENV" == "dev" ]]; then
  log_info "Starting next dev…"
  npm run dev &
  FRONTEND_PID=$!
else
  log_info "Building Next.js (production)…"
  npm run build
  log_info "Starting next start…"
  npm run start &
  FRONTEND_PID=$!
fi

# ── Wait + traps ───────────────────────────────────────────────────────
cleanup() {
  log_warn "Stopping (SIGINT / SIGTERM)…"
  kill "$BACKEND_PID"  2>/dev/null || true
  kill "$FRONTEND_PID" 2>/dev/null || true
  wait "$BACKEND_PID"  2>/dev/null || true
  wait "$FRONTEND_PID" 2>/dev/null || true
  log_ok "Stopped."
  exit 0
}
trap cleanup SIGINT SIGTERM

log_section "Running"
log_info  "Backend  PID $BACKEND_PID  → http://localhost:3001"
log_info  "Frontend PID $FRONTEND_PID → http://localhost:3000"
log_info  "Logs:    /var/MindPrism/${ENV}/logs/"
log_info  "Ctrl+C to stop"
wait
