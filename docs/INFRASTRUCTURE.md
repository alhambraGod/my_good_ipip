# MindPrism — Infrastructure & Horizontal Scale

> How nginx, the frontend pool, and the backend pool fit together —
> and how to grow each pool from 1 → N without rewriting the world.
> Pair with **DEPLOYMENT_digitalocean.md** for the sized cost recipes
> and **DEPLOYMENT_docker.md** for the run-a-container details.

---

## 1. The shape

```
                                ┌────────────────────────┐
                                │  Cloudflare (free CDN) │
                                └───────────┬────────────┘
                                            │ TLS terminated at edge
                                            ▼
                              ┌──────────────────────────┐
                              │  nginx (1 per host)      │
                              │  /etc/nginx/nginx.conf   │
                              │  conf.d/mindprism.*.conf │
                              └──────────┬────────┬──────┘
                                         │        │
              upstream mindprism_frontend│        │upstream mindprism_backend
                                         │        │
              ┌──────────────────────────┘        └──────────────────────────┐
              │                                                              │
   ┌──────────┴──────────┐                                          ┌────────┴───────────┐
   │  Next.js × N        │                                          │  FastAPI × M       │
   │  (port 3000)        │                                          │  gunicorn 2 workers│
   │  static assets +    │                                          │  /api/v3/*         │
   │  /api/og/[id]       │                                          │  /s/{code}         │
   └─────────────────────┘                                          └─────────┬──────────┘
                                                                              │
                                                            mysql+pymysql DSN │
                                                                              ▼
                                                              ┌───────────────────────┐
                                                              │  MySQL 8              │
                                                              │  dev: container       │
                                                              │  prod: host process   │
                                                              │  growth: managed DB   │
                                                              └───────────────────────┘
```

**Key invariant.** Frontend and backend are **stateless**. Nothing on
disk except logs. Anything that needs to live across requests is in
MySQL (or Valkey at higher tiers). This is why we can scale by saying
"give me 4 more backend pods" without touching the rest.

---

## 2. nginx config — what each block does

`nginx/` ships three files that are **identical across tiers** — only
the upstream pool changes:

```
nginx/
├── nginx.conf                      ← global: workers, gzip, log_format,
│                                     rate-limit zones, cache stores
└── conf.d/
    ├── _proxy_common.inc           ← shared `proxy_set_header`, timeouts,
    │                                  `proxy_next_upstream` retry
    ├── mindprism.dev.conf          ← dev site: /api/* → backend, / → frontend
    └── mindprism.prod.conf         ← prod site: + HTTPS + CSP + LE certs
```

The dev/prod configs are 95% identical; the prod one adds:
- `:443 ssl http2` server with Let's Encrypt cert paths
- HSTS, CSP (Razorpay-aware), Permissions-Policy headers
- HTTP→HTTPS redirect
- `/docs` Swagger UI returns 404
- payment webhook excluded from rate limit

### Hot endpoints

| Path pattern | Upstream | Special handling |
| --- | --- | --- |
| `/api/v3/payment/webhook/razorpay` | backend | **no rate limit** (signed payload) |
| `/api/v3/payment/*` , `/api/v3/auth/*`, `/api/auth/*` | backend | `pay_zone` (5 r/s, burst 10) |
| `/api/*` (default) | backend | `api_zone` (30 r/s, burst 60) |
| `/s/{code}` | backend | `api_zone` |
| `/api/og/{id}` | frontend (Next route) | nginx cache 5 min, `proxy_cache_lock` |
| `/_next/static`, `/favicon.ico`, `/robots.txt`, `/sitemap.xml` | frontend | nginx cache 1 day, `Cache-Control: immutable` |
| `/` and everything else | frontend | passthrough |

---

## 3. How to scale-out (3 levels)

### A. Same host, more containers (1×→1 host, more replicas)

This is the **first** thing you do when latency rises. It's free in
terms of nginx config edits — Docker Compose's built-in DNS
round-robins service-name resolution.

```bash
# Run more backend replicas on the same host:
sudo bash deploy/scale.sh prod backend=3
# Now backend:3001 resolves round-robin to backend-1, backend-2, backend-3.
docker compose -f docker-compose.prod.yml ps
```

Capacity: 1 vCPU host → ~150 RPS for `backend=2`. Going from
`backend=2` to `backend=4` on a `s-2vcpu-4gb` ($24/mo) Droplet
roughly doubles throughput up to ~600 RPS.

### B. Multiple hosts (multi-Droplet)

When the single Droplet is saturated. Spin up additional Droplets
running **only** the backend container (no nginx, no frontend), then
add their private IPs to nginx's upstream block. Use DigitalOcean VPC
or Tailscale for the private mesh — you do NOT want backend `:3001`
exposed publicly.

```nginx
# nginx/conf.d/mindprism.prod.conf
upstream mindprism_backend {
    least_conn;
    server backend:3001 max_fails=3 fail_timeout=15s;     # local container
    server 10.114.0.11:3001 max_fails=3 fail_timeout=15s; # second Droplet
    server 10.114.0.12:3001 max_fails=3 fail_timeout=15s; # third Droplet
    server 10.114.0.13:3001 backup;                       # cold standby
    keepalive 64;
}
```

Then `nginx -s reload` (no traffic interruption — old workers drain).

### C. Multi-region (regional active-active)

When a single region's tail latency hurts. DO Global LB sits in front;
each region runs its own DOKS cluster (or Droplet pool). DB layer:
Managed MySQL primary in BLR1 + read-replica in SGP1. Razorpay webhook
endpoint is single-region (BLR1) to avoid duplicate-confirm races.

This is **Tier 3** and is documented in `DEPLOYMENT_digitalocean.md`.

---

## 4. Logging at scale

Every container writes to `/var/MindPrism/<env>/logs/` via a host bind
mount. `services/logging_setup.py`:

- One file per stream (`app.log`, `error.log`, `access.log`).
- Rotation: nightly at midnight (`TimedRotatingFileHandler when=midnight`).
- Archives go to `logs/history/app.log.YYYY-MM-DD`.
- `LOG_RETENTION_DAYS=30` keeps the last 30 days, then deletes.

When you scale beyond 1 host, ship logs to a central store. Two paths:

| Path | What it costs | Verdict |
| --- | --- | --- |
| **DO Monitoring + Logtail** | $0.20 / GB ingested | Easiest. Drops in via journald or filebeat. |
| **Self-hosted Loki + Promtail** | infra you run | More control, higher ops burden. |

Either way, the per-host file rotation we already do gives you a
2-day window to catch a problem locally even if shipping is broken.

---

## 5. Common scale-out mistakes (and the fix)

| Mistake | Why it hurts | Fix |
| --- | --- | --- |
| Storing JWT blacklist in app memory | Replica A can't see Replica B's logout | Move to Valkey / managed cache |
| Razorpay order created on Replica A, verify hits Replica B | the verify path doesn't strictly need stickiness (we re-fetch the assessment by `payment_txn_id`), but in-flight rate-limit counters do | sticky-cookie on `/api/v3/payment/` (already in DO LB recipe) or move counters to Valkey |
| nginx `proxy_pass` with bare IP, no DNS TTL | Compose IPs change on `down/up` | use the **service name** (`backend:3001`), nginx auto-resolves |
| Two replicas writing the same log file | interleaved log lines | We use `bind: /var/MindPrism/$ENV → /var/MindPrism/$ENV` so each container has its own pid; logs land in the same file but are tagged with `[svc-name]` from logging_setup. Aggregator dedupes by `(host, container_id, ts)`. |
| Letsencrypt renewals on multi-host | only the LB host can answer ACME challenge | Run certbot on the LB host; copy the cert to other hosts (or use DNS-01 instead of HTTP-01) |

---

## 6. Health + readiness

| Endpoint | What it does |
| --- | --- |
| `GET /api/health` (backend)            | returns `{status:"ok",service:"mindprism"}` — used by docker / nginx healthcheck |
| `HEAD /` (frontend)                    | Next.js healthy when 200 |
| `GET / ` via nginx                     | end-to-end check |

Docker compose ships:
- `backend.healthcheck` → `curl /api/health`, 30s interval
- `frontend.healthcheck` → `wget /`, 30s interval
- `mysql.healthcheck` → `mysqladmin ping`, 5s interval, 20 retries

When a replica fails its healthcheck, nginx's `max_fails=3
fail_timeout=15s` excludes it from the pool until the next health
window passes.
