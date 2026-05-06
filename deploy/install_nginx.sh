#!/usr/bin/env bash
# Install nginx on the host AND drop our config files into /etc/nginx/.
# Use when running "native" (no Docker) so nginx is part of the host.
# When running Docker, nginx is part of docker-compose so this script is unneeded.
#
# Usage: sudo bash deploy/install_nginx.sh [dev|prod]

set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
# shellcheck disable=SC1091
source "$HERE/_lib.sh"

[[ "$(id -u)" == "0" ]] || die "Run as root (use sudo)."

ENV="${1:-prod}"
[[ "$ENV" == "dev" || "$ENV" == "prod" ]] || die "Usage: $0 <dev|prod>"

log_section "Install + configure nginx ($ENV)"

if ! command -v nginx >/dev/null 2>&1; then
  log_info "Installing nginx via apt…"
  apt-get update -qq
  apt-get install -y nginx
fi

systemctl enable nginx

log_info "Copying config files"
install -m 0644 "$ROOT/nginx/nginx.conf" /etc/nginx/nginx.conf
install -d -m 0755 /etc/nginx/conf.d
install -m 0644 "$ROOT/nginx/conf.d/_proxy_common.inc"      /etc/nginx/conf.d/_proxy_common.inc
install -m 0644 "$ROOT/nginx/conf.d/mindprism.${ENV}.conf"  /etc/nginx/conf.d/default.conf

# Cache directories used by nginx.conf.
install -d -m 0755 /var/cache/nginx/static /var/cache/nginx/og

# When NOT in Docker, nginx upstreams have to point at 127.0.0.1.
log_info "Patching upstream targets to 127.0.0.1 (native deploy)"
sed -i 's|server backend:3001|server 127.0.0.1:3001|g'   /etc/nginx/conf.d/default.conf
sed -i 's|server frontend:3000|server 127.0.0.1:3000|g'  /etc/nginx/conf.d/default.conf

log_info "nginx -t…"
nginx -t

log_info "Restarting nginx"
systemctl restart nginx
log_ok "nginx is serving on :80 (and :443 in prod after certbot)."
