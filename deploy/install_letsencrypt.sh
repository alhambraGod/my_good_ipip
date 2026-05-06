#!/usr/bin/env bash
# Install certbot + issue a Let's Encrypt cert for the given domain.
#
# Usage: sudo bash deploy/install_letsencrypt.sh DOMAIN [EMAIL]
#   DOMAIN    e.g. www.mindprism.in
#   EMAIL     contact email (defaults to ops@DOMAIN)

set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$HERE/_lib.sh"

[[ "$(id -u)" == "0" ]] || die "Run as root (use sudo)."
DOMAIN="${1:-}"
[[ -n "$DOMAIN" ]] || die "Usage: $0 DOMAIN [EMAIL]"
EMAIL="${2:-ops@$DOMAIN}"

log_section "Install certbot + issue cert for $DOMAIN"

if ! command -v certbot >/dev/null 2>&1; then
  apt-get update -qq
  apt-get install -y certbot python3-certbot-nginx
fi

# Ensure ACME challenge dir exists.
install -d -m 0755 /var/www/certbot

certbot --nginx \
  --non-interactive \
  --agree-tos \
  --email "$EMAIL" \
  -d "$DOMAIN" \
  --redirect

log_ok "Cert at /etc/letsencrypt/live/$DOMAIN/"
log_info "Auto-renewal is enabled via the certbot.timer systemd unit."
