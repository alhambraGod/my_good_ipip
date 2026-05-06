#!/usr/bin/env bash
# Shared helpers for the deploy/ scripts.
# Source this from each script: `source "$(dirname "$0")/_lib.sh"`

set -euo pipefail

# ── Logging utilities ──────────────────────────────────────────────────
COLOR_RESET='\033[0m'
COLOR_GREEN='\033[32m'
COLOR_YELLOW='\033[33m'
COLOR_RED='\033[31m'
COLOR_BLUE='\033[34m'
COLOR_BOLD='\033[1m'

log_info()    { printf "${COLOR_BLUE}➜${COLOR_RESET} %s\n" "$*"; }
log_ok()      { printf "${COLOR_GREEN}✓${COLOR_RESET} %s\n" "$*"; }
log_warn()    { printf "${COLOR_YELLOW}⚠${COLOR_RESET} %s\n" "$*"; }
log_error()   { printf "${COLOR_RED}✗${COLOR_RESET} %s\n" "$*" >&2; }
log_section() {
  printf "\n${COLOR_BOLD}====================  %s  ====================${COLOR_RESET}\n" "$*"
}

die() { log_error "$*"; exit 1; }

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Missing required command: $1"
}

# Ensure log dirs exist with the right ownership.
ensure_log_dirs() {
  local env="$1"  # dev | prod
  local root="${LOG_ROOT_HOST:-/var/MindPrism}/${env}"
  if ! mkdir -p "${root}/logs" "${root}/logs/history" "${root}/logs/nginx" 2>/dev/null; then
    log_warn "Need sudo to create ${root}; running with sudo…"
    sudo mkdir -p "${root}/logs" "${root}/logs/history" "${root}/logs/nginx"
    sudo chmod 0775 "${root}" "${root}/logs" "${root}/logs/history" "${root}/logs/nginx"
  fi
  log_ok "Log dir ready: ${root}/logs"
}

# Validate env arg (dev|prod) and source env/{env}.env if present.
load_env_file() {
  local env="$1"
  local repo_root="$2"
  local env_file="${repo_root}/env/${env}.env"
  if [[ -f "$env_file" ]]; then
    log_info "Loading ${env_file}"
    # Export every var, including those with quotes/spaces.
    set -a
    # shellcheck disable=SC1090
    source "$env_file"
    set +a
  else
    log_warn "${env_file} not found — using existing shell env."
  fi
}

# Verify the env arg and pick the right docker-compose file.
pick_compose_file() {
  local env="$1"
  case "$env" in
    dev)  echo "docker-compose.dev.yml" ;;
    prod) echo "docker-compose.prod.yml" ;;
    *)    die "Invalid environment: $env (use dev or prod)" ;;
  esac
}
