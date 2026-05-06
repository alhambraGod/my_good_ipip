# MindPrism — Container Deployment Guide

End-to-end recipes for running MindPrism in Docker (the recommended
path) **and** without Docker (native install). Two environments: `dev`
and `prod`.

> Pair this with **deployment-digitalocean.md** for sized recipes,
> **infrastructure.md** for the nginx + scale-out story, and
> **runbook-payments.md** for going live with Razorpay.

---

## 0. Operating layout (both Docker and native)

| Path on host | Purpose |
| --- | --- |
| `/var/MindPrism/dev/logs/`     | dev runtime logs (`app.log`, `access.log`, `error.log`) |
| `/var/MindPrism/dev/logs/history/` | rotated archives, suffixed `app.log.YYYY-MM-DD` |
| `/var/MindPrism/dev/logs/nginx/`   | nginx access + error logs (when running through Docker) |
| `/var/MindPrism/prod/logs/...` | same, prod |
| `/etc/nginx/conf.d/`           | nginx config files (native deploy) |
| `/etc/letsencrypt/`            | LE certs (prod TLS) |

Logs are emitted by the FastAPI process via `services/logging_setup.py`.
Rotation: nightly at midnight, archived files keep 30 days
(`LOG_RETENTION_DAYS`).

---

## 1. Docker — dev

`docker-compose.dev.yml` wires up four containers on a private network
(`mindprism-dev`):

| Service | Image | Port | Notes |
| --- | --- | --- | --- |
| **mysql**    | mysql:8.0           | 127.0.0.1:3307 | password = `mindprism_dev`; data volume `mindprism-dev-mysql` |
| **backend**  | mindprism-backend:dev | 127.0.0.1:3001 | gunicorn 2 workers; FastAPI |
| **frontend** | mindprism-frontend:dev | 127.0.0.1:3000 | next start (production build) |
| **nginx**    | nginx:1.27-alpine   | 80             | reverse proxy + cache + rate-limit |

### Bring up

```bash
git clone <repo> mindprism && cd mindprism
sudo bash deploy/start_docker.sh dev
# … wait for healthchecks …
curl -I http://localhost                 # 200 → frontend via nginx
curl  http://localhost/api/health        # {"status":"ok",...}
```

### Tear down

```bash
sudo bash deploy/stop_docker.sh dev               # stops, keeps volumes
sudo bash deploy/stop_docker.sh dev --volumes     # also wipes mysql data
```

### Inspect

```bash
docker compose -f docker-compose.dev.yml logs -f backend
docker compose -f docker-compose.dev.yml exec mysql mysql -uroot -p
sudo tail -f /var/MindPrism/dev/logs/app.log
```

---

## 2. Docker — prod

`docker-compose.prod.yml` runs **only** nginx + frontend + backend.
MySQL lives on the host (installed via `deploy/install_mysql_prod.sh`)
and is reached via `host.docker.internal` (this works on Linux 20.10+
when the compose file declares `extra_hosts:
host.docker.internal:host-gateway`).

### One-time host setup

```bash
# 1. Install host MySQL
MYSQL_ROOT_PASSWORD='strong-pwd' \
MYSQL_PASSWORD='another-strong-pwd' \
sudo bash deploy/install_mysql_prod.sh
# (prints the DATABASE_URL to paste into env/prod.env)

# 2. Edit env/prod.env (DATABASE_URL, RAZORPAY_*, JWT_SECRET, etc.)
nano env/prod.env

# 3. (optional) Issue a TLS cert
sudo bash deploy/install_letsencrypt.sh www.mindprism.in
```

### Bring up + scale

```bash
sudo bash deploy/start_docker.sh prod                        # initial 1×1
sudo bash deploy/scale.sh        prod backend=3 frontend=2   # scale up
docker compose -f docker-compose.prod.yml ps
```

`nginx` doesn't need to reload after `scale` — Docker Compose's DNS
returns the live replica pool on every query, and our nginx config uses
hostnames (`server backend:3001`) instead of fixed IPs, so each new
upstream resolution picks up new replicas automatically.

### Update without downtime

```bash
git pull
sudo bash deploy/start_docker.sh prod --build       # rebuilds images
docker compose -f docker-compose.prod.yml up -d --no-deps backend frontend
```

Compose default `restart: unless-stopped` + nginx upstream
`max_fails=3 fail_timeout=15s` give a smooth rolling-restart.

---

## 3. Native — dev

For laptops without Docker:

```bash
# Tools needed: Python 3.11, Node 20+, optional MySQL 8 on host.
bash deploy/start_native.sh dev
# DB falls back to sqlite:///./mindprism_dev.db if no MySQL is reachable
# (set DATABASE_URL beforehand to point at one if you have it).
```

The native start script does *not* run nginx. The frontend talks to the
backend directly via `NEXT_PUBLIC_API_URL`.

For a more "production-like" laptop run with nginx:

```bash
sudo bash deploy/install_nginx.sh dev      # /etc/nginx/* → our config
sudo systemctl reload nginx
```

---

## 4. Native — prod

Use this if you've already provisioned the host (e.g. Ubuntu Droplet)
and want bare metal performance / observability. Equivalent to the
Docker prod tier, just without Docker.

```bash
# 1. Install MySQL on the host
sudo bash deploy/install_mysql_prod.sh

# 2. Install nginx + drop our config
sudo bash deploy/install_nginx.sh prod

# 3. Start backend + frontend (foreground; use systemd unit in real prod)
bash deploy/start_native.sh prod
```

### systemd integration (recommended for prod-native)

`/etc/systemd/system/mindprism-backend.service`:

```ini
[Unit]
Description=MindPrism backend (FastAPI)
After=network.target mysql.service
Wants=mysql.service

[Service]
Type=simple
User=mindprism
WorkingDirectory=/opt/mindprism/backend
EnvironmentFile=/opt/mindprism/backend/.env
ExecStart=/opt/mindprism/.venv/bin/gunicorn main:app \
  --bind 0.0.0.0:3001 \
  --workers ${GUNICORN_WORKERS} \
  --worker-class uvicorn.workers.UvicornWorker \
  --timeout 60 --keep-alive 5 \
  --access-logfile - --error-logfile -
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

`/etc/systemd/system/mindprism-frontend.service`:

```ini
[Unit]
Description=MindPrism frontend (Next.js)
After=network.target

[Service]
Type=simple
User=mindprism
WorkingDirectory=/opt/mindprism/frontend
EnvironmentFile=/opt/mindprism/frontend/.env.local
ExecStart=/usr/bin/npm run start
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable + start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now mindprism-backend mindprism-frontend
```

---

## 5. Environment variables (full list)

| Var | Tier | Default | What it does |
| --- | --- | --- | --- |
| `APP_ENV` | core | `dev` | one of `dev` / `stage` / `prod` |
| `DATABASE_URL` | core | sqlite | SQLAlchemy URL — `mysql+pymysql://...` in prod |
| `LOG_ROOT` | core | `/var/MindPrism` | base dir for centralised logs |
| `LOG_FALLBACK_ROOT` | core | `./logs` | used if `LOG_ROOT` is unwritable |
| `LOG_RETENTION_DAYS` | core | `30` | history archive retention |
| `FRONTEND_URL` | core | `http://localhost:3000` | CORS allowlist + auth callback host |
| `API_PUBLIC_URL` | core | `http://localhost:3001` | what `/s/{code}` short links resolve to |
| `JWT_SECRET` | core | dev default | **must override in prod** |
| `OAUTH_STATE_SECRET` | core | empty | Twitter/Telegram CSRF guard |
| `PAYMENT_MODE` | payment | `mock` | `razorpay` for live |
| `RAZORPAY_KEY_ID` | payment | empty | `rzp_test_*` or `rzp_live_*` |
| `RAZORPAY_KEY_SECRET` | payment | empty | secret for HMAC signing |
| `RAZORPAY_WEBHOOK_SECRET` | payment | empty | webhook HMAC verification |
| `PROMO_MAX_REDEMPTIONS` | pricing | 1000 | promo cap |
| `PRICE_FULL_INR` / `PRICE_PROMO_INR` | pricing | 99 / 49 | display price |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | auth | empty | Google OAuth |
| `META_APP_ID` / `META_APP_SECRET` | auth | empty | WhatsApp OAuth |
| `FACEBOOK_APP_ID` / `FACEBOOK_APP_SECRET` | auth | empty | Facebook OAuth |
| `NEXT_PUBLIC_API_URL` | frontend | `http://localhost:3001` | browser-side API base |
| `NEXT_PUBLIC_SITE_URL` | frontend | `http://localhost:3000` | for OG metadata + sitemap |

Central source files: `env/dev.env` + `env/prod.env`. Deploy scripts
read those, generate `backend/.env` and `frontend/.env.local`.

---

## 6. Image build matrix

| Image | Base | Size (compressed) | Layers |
| --- | --- | --- | --- |
| `mindprism-backend` | python:3.11-slim | ~280 MB | apt + pip + app |
| `mindprism-frontend` | node:20-alpine | ~200 MB | deps → builder → runtime (multi-stage) |
| `nginx` | nginx:1.27-alpine | 23 MB | upstream image |
| `mysql` (dev only) | mysql:8.0 | 600 MB | upstream image |

Build args you can pass on the CLI:

```bash
docker compose -f docker-compose.prod.yml build \
  --build-arg NEXT_PUBLIC_API_URL=https://api.mindprism.in \
  --build-arg NEXT_PUBLIC_SITE_URL=https://mindprism.in
```

---

## 7. Backup + restore

### MySQL — dev (in-container)

```bash
# Dump
docker compose -f docker-compose.dev.yml exec mysql \
  mysqldump -uroot -pmindprism_dev mindprism_dev | gzip \
  > /var/MindPrism/dev/logs/db-$(date +%F).sql.gz

# Restore
gunzip -c db-2026-05-06.sql.gz | docker compose -f docker-compose.dev.yml exec -T mysql \
  mysql -uroot -pmindprism_dev mindprism_dev
```

### MySQL — prod (host install)

```bash
mysqldump -u mindprism -p mindprism_prod | gzip \
  > /var/MindPrism/prod/logs/db-$(date +%F).sql.gz
```

Schedule it via cron:

```cron
# /etc/cron.d/mindprism-mysqldump
0 2 * * *   mindprism   mysqldump -u mindprism -p"$MYSQL_PASSWORD" mindprism_prod | gzip > /var/MindPrism/prod/logs/history/db-$(date +\%F).sql.gz
0 3 * * *   mindprism   find /var/MindPrism/prod/logs/history -name 'db-*.sql.gz' -mtime +30 -delete
```

---

## 8. Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `host.docker.internal` doesn't resolve in containers | Old Docker / non-Linux | Add `--add-host=host.docker.internal:host-gateway`; on macOS it's automatic |
| `MySQL 1130: Host '...' is not allowed to connect` | bind-address only `127.0.0.1` | Run `install_mysql_prod.sh` with `MYSQL_BIND_HOST=0.0.0.0` (only behind a firewall) |
| `nginx: bind() to 0.0.0.0:80 failed (98: Address already in use)` | host nginx already running | `sudo systemctl stop nginx` before `start_docker.sh` |
| Backend logs missing | `LOG_ROOT` unwritable inside container | Confirm bind mount: `/var/MindPrism/$ENV` exists and is `chmod 0775` |
| `502 Bad Gateway` on / | One of frontend / backend unhealthy | `docker compose ps`; `docker compose logs <svc>` |
| Razorpay verify fails despite signing-rule match | `RAZORPAY_KEY_SECRET` differs between containers (rolling deploy) | Make sure all backend replicas read the same env file |
| Letsencrypt renewal fails | port 80 not reachable / DNS not pointed | `nslookup mindprism.in` + `ufw status` |

