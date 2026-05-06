#!/usr/bin/env bash
# Install + bootstrap a host-level MySQL 8 on Ubuntu (Debian-family).
# Idempotent: reruns are safe.
#
# Usage:  sudo bash deploy/install_mysql_prod.sh
# Env:    MYSQL_ROOT_PASSWORD (required)
#         MYSQL_DATABASE      default: mindprism_prod
#         MYSQL_USER          default: mindprism
#         MYSQL_PASSWORD      required
#         MYSQL_BIND_HOST     default: 127.0.0.1 (bind to localhost only)

set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$HERE/_lib.sh"

[[ "$(id -u)" == "0" ]] || die "Run as root (use sudo)."

: "${MYSQL_ROOT_PASSWORD:?MYSQL_ROOT_PASSWORD must be set}"
: "${MYSQL_PASSWORD:?MYSQL_PASSWORD must be set}"
MYSQL_DATABASE="${MYSQL_DATABASE:-mindprism_prod}"
MYSQL_USER="${MYSQL_USER:-mindprism}"
MYSQL_BIND_HOST="${MYSQL_BIND_HOST:-127.0.0.1}"

log_section "Install MySQL 8 (host-level, prod)"

if ! command -v mysql >/dev/null 2>&1; then
  log_info "Installing mysql-server…"
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq
  apt-get install -y mysql-server
fi

systemctl enable --now mysql

# Bind address: by default lock down to 127.0.0.1; use 0.0.0.0 only behind
# a private VPC + firewall rules.
CONF=/etc/mysql/mysql.conf.d/mysqld.cnf
if [[ -f "$CONF" ]]; then
  log_info "Setting bind-address=$MYSQL_BIND_HOST and utf8mb4 defaults"
  sed -i -E "s/^[# ]*bind-address.*/bind-address = $MYSQL_BIND_HOST/" "$CONF"
  if ! grep -q "character_set_server" "$CONF"; then
    cat >> "$CONF" <<'EOF'

# MindPrism additions
character_set_server = utf8mb4
collation_server     = utf8mb4_unicode_ci
max_connections      = 200
EOF
  fi
  systemctl restart mysql
fi

log_info "Creating database + user (idempotent)"
mysql --user=root --password="$MYSQL_ROOT_PASSWORD" <<EOF || mysql --user=root <<EOF
CREATE DATABASE IF NOT EXISTS \`$MYSQL_DATABASE\`
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '$MYSQL_USER'@'127.0.0.1' IDENTIFIED BY '$MYSQL_PASSWORD';
CREATE USER IF NOT EXISTS '$MYSQL_USER'@'%'         IDENTIFIED BY '$MYSQL_PASSWORD';
GRANT ALL PRIVILEGES ON \`$MYSQL_DATABASE\`.* TO '$MYSQL_USER'@'127.0.0.1';
GRANT ALL PRIVILEGES ON \`$MYSQL_DATABASE\`.* TO '$MYSQL_USER'@'%';
FLUSH PRIVILEGES;
EOF

log_ok "MySQL ready."
log_info "Connection URL (paste into env/prod.env DATABASE_URL):"
cat <<EOF

  mysql+pymysql://$MYSQL_USER:$MYSQL_PASSWORD@host.docker.internal:3306/$MYSQL_DATABASE?charset=utf8mb4

  (Inside Docker prod compose, host.docker.internal resolves to the host;
   on bare-metal, replace with 127.0.0.1.)

EOF
