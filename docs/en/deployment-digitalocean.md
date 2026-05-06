# MindPrism — DigitalOcean Deployment

> Four sized recipes (10 / 100 / 1,000 / 10,000 QPS) on DigitalOcean.
> Pricing from [digitalocean.com/pricing](https://www.digitalocean.com/pricing).
> All tiers ship with the **same code** — the difference is *how many*
> containers, on *how many* hosts, behind nginx.
>
> See **deployment-docker.md** for the container-by-container spec
> (`docker-compose.{dev,prod}.yml`, Dockerfiles, env), and **infrastructure.md**
> for the cross-tier nginx + scale-out story.

---

## 0. Capacity model — what does 1 QPS mean?

MindPrism's hot endpoints have very different costs:

| Endpoint | Type | Hot path | DB cost | Latency budget |
| --- | --- | --- | --- | --- |
| `GET /` (landing) | Next ISR HTML | static asset | 0 | ≤ 100ms TTFB |
| `GET /archetypes(/[cell])` | Next ISR | static asset (10-min revalidate) | 0 | ≤ 100ms TTFB |
| `GET /api/v3/archetypes(/...)` | FastAPI read | `cells.json` LRU cache | 0 | ≤ 30ms |
| `GET /api/v3/payment/price` | FastAPI read | 1 row count | 1 SELECT | ≤ 30ms |
| `GET /api/v3/assessment/demographic` | FastAPI read | static py | 0 | ≤ 20ms |
| `POST /api/v3/assessment/start` | FastAPI write | 1 INSERT | 1 INSERT | ≤ 80ms |
| `POST /api/v3/assessment/submit` | FastAPI write + score | scoring math (~5–15ms CPU) | 1 UPDATE + 1 INSERT (ShortLink) | ≤ 200ms |
| `GET /api/v3/assessment/{id}/results` | FastAPI read | 1 row + cell content from cache | 1 SELECT | ≤ 50ms |
| `POST /api/v3/payment/razorpay/order` | FastAPI write + outbound HTTPS | Razorpay API call (300–800ms upstream) | 1 UPDATE | ≤ 1s |
| `POST /api/v3/payment/razorpay/verify` | FastAPI write | HMAC verify | 1 UPDATE | ≤ 50ms |
| `POST /api/v3/payment/webhook/razorpay` | FastAPI write | HMAC verify | 1 UPDATE | ≤ 50ms |
| `GET /api/v3/report/{id}` | FastAPI read | 1 row + cell + 5+ careers | 1 SELECT | ≤ 100ms |
| `GET /s/{code}` | FastAPI read + 302 | 1 SELECT + 1 UPDATE | 2 ops | ≤ 30ms |
| `GET /api/og/[id]` | Next nodejs runtime, fetch backend | 1 backend GET | 1 SELECT (via API) | ≤ 600ms |

For sizing we assume the **average request mix** at peak:

```
landing/archetypes (CDN + ISR)  60%   ← ~0 backend cost
quiz reads                      20%   ← p95 < 30ms backend
quiz writes (start + submit)    10%   ← p95 < 200ms backend
paywall + report                 8%   ← p95 < 100ms backend (Razorpay async)
share + OG                       2%   ← p95 < 600ms (image) / < 30ms (short)
```

A single uvicorn worker on 0.5 vCPU sustains ~75 RPS of "average mix"
traffic before p99 latency degrades. Two workers on 1 vCPU → ~150 RPS.

---

## 1. Tier 0 "Bootstrap" — up to 10 QPS, **≤ $20 / month**

**Goal:** weekend launch / first 50 users / share with friends. Single
$12 Droplet runs **everything** in Docker; same compose file you'll
later split across hosts.

### Architecture

```
                 Cloudflare CDN (free)
                          │
                          ▼
            ┌─────────────────────────────┐
            │  Single Droplet  s-1vcpu-2gb │  $12/mo
            │  Ubuntu 24.04 + Docker      │
            │                             │
            │  docker-compose.prod.yml    │
            │  ├── nginx :80,443          │
            │  ├── frontend :3000         │
            │  ├── backend  :3001         │
            │  └── (host) MySQL 8         │  ← installed via deploy/install_mysql_prod.sh
            │                             │
            │  /var/MindPrism/prod/logs/  │  ← bind-mounted into containers
            └─────────────────────────────┘
                       │
                       ▼
            ┌─────────────────────────────┐
            │  Spaces (S3-compat)         │  $5/mo (250 GB + 1 TB egress)
            │  PDF reports + OG cards     │
            └─────────────────────────────┘
```

### Pricing

| Item | Cost (USD) | Source |
| --- | --- | --- |
| Droplet `s-1vcpu-2gb` | **$12** | [DO pricing](https://www.digitalocean.com/pricing) — Droplets from $4/mo, this SKU is the smallest with enough RAM for 4 containers + MySQL |
| Backups (20% of Droplet) | $2.40 | DO weekly backup, 4-week retention |
| Spaces (object storage) | $5 | S3-compatible, includes built-in CDN |
| **Total** | **≈ $19.40 / mo** | comfortably ≤ $20 budget |

> **Why a single Droplet (not App Platform)?** App Platform's smallest
> tier (`basic-xxs`) is $12/mo per service; we'd need at least two,
> blowing the $20 budget. Droplet gives us all four containers + host
> MySQL within the budget, at the cost of doing OS upgrades ourselves.

### Step-by-step deploy

```bash
# On a fresh Ubuntu 24.04 Droplet (logged in as root):
apt-get update -qq && apt-get install -y git docker.io docker-compose-v2

# 1. Clone the repo
git clone https://github.com/<your-org>/mindprism.git /opt/mindprism
cd /opt/mindprism

# 2. Install host MySQL
MYSQL_ROOT_PASSWORD='strong-pwd-here' \
MYSQL_PASSWORD='another-strong-pwd' \
sudo bash deploy/install_mysql_prod.sh

# 3. Edit env/prod.env: paste the connection URL printed at the end of step 2,
#    plus FRONTEND_URL, API_PUBLIC_URL, NEXT_PUBLIC_*, RAZORPAY_*, JWT_SECRET.
nano env/prod.env

# 4. Bring up the stack
sudo bash deploy/start_docker.sh prod

# 5. Verify
curl -I http://localhost              # via nginx → frontend → 200
curl -s http://localhost/api/health   # → {"status":"ok",...}
```

### Capacity check (this tier)
- nginx + frontend + backend on 1 vCPU / 2 GB. Backend `gunicorn -w 2`
  → ~150 RPS average mix.
- 10 QPS target = 7 % utilisation; massive headroom for traffic
  spikes.
- Host MySQL on the same box: 8.0 InnoDB at default settings handles
  500+ TPS — 50× headroom.
- Memory budget: nginx 30 MB + frontend 250 MB + backend 200 MB +
  MySQL 350 MB ≈ 830 MB used, 1.2 GB free for OS / page cache.

### Operational
- **Backups.** DO automated backups (image-level) + a nightly cron
  that does `mysqldump > /var/MindPrism/prod/logs/db-$(date).sql.gz`
  (set this up via the runbook in deployment-docker.md).
- **Monitoring.** Free DO Monitoring + Uptime check. Alert on
  Droplet CPU > 75% / disk > 80% / 5xx rate > 1%.
- **TLS.** `sudo bash deploy/install_letsencrypt.sh www.mindprism.in`
  issues a Let's Encrypt cert and wires it into nginx prod conf.

---

## 2. Tier 1 "Launch" — up to 100 QPS, ~5,000 daily completions

**Goal:** post-product-hunt / WhatsApp-share viral spike survives
without operator panic.

### Architecture (delta from Tier 0)

- Bump Droplet to **`s-2vcpu-4gb` ($24)** to get 2 vCPUs.
- **Scale frontend + backend horizontally** on the SAME Droplet via
  `bash deploy/scale.sh prod backend=2 frontend=2`. nginx round-robins
  the docker-internal DNS — no nginx-config edit needed.

### Pricing

| Item | Cost (USD) |
| --- | --- |
| Droplet `s-2vcpu-4gb` | $24 |
| Backups (20%) | $4.80 |
| Spaces 250 GB | $5 |
| **Total** | **≈ $33.80 / mo** |

(Or move MySQL to **DO Managed Postgres / MySQL `db-s-1vcpu-1gb`**
($15) and use a `s-1vcpu-2gb` ($12) Droplet ⇒ $32 — preferred long
term, but slightly more $ at this tier.)

### Capacity
- 4 backend workers (2 instances × 2 workers each) → ~600 RPS.
- 100 QPS target = 17% utilisation.
- Same host MySQL works; if you want PITR + automated failover, move
  to Managed DB at this tier (it's the same env-var change).

---

## 3. Tier 2 "Growth" — up to 1,000 QPS, ~100,000 daily completions

**Goal:** post-launch organic + WhatsApp viral; multi-instance,
single region (BLR1) but horizontally scalable.

### Architecture

```
                       Cloudflare CDN
                             │
                             ▼
                    ┌────────────────┐
                    │ DO Load Balancer│  $12/mo
                    └───────┬────────┘
                            │
          ┌─────────────────┼─────────────────┐
          ▼                                   ▼
┌─────────────────────┐               ┌─────────────────────┐
│ Droplet s-2vcpu-4gb │               │ Droplet s-2vcpu-4gb │
│ frontend × 2        │               │ frontend × 2        │
│ backend × 2         │               │ backend × 2         │
│ nginx (private)     │               │ nginx (private)     │
│ ($24/mo)            │               │ ($24/mo)            │
└─────────────────────┘               └──────────┬──────────┘
                                                 │
                                  ┌──────────────┼──────────────┐
                                  ▼                             ▼
                       ┌──────────────────┐          ┌──────────────────┐
                       │ Managed MySQL    │          │ Managed Valkey   │
                       │ Production tier  │          │ (Redis-compat)   │
                       │ 4 GB / 2 vCPU /  │          │ 1 GB / 1 vCPU    │
                       │ 38 GB / standby  │          │ ($30/mo)         │
                       │ ($120/mo)        │          └──────────────────┘
                       └──────────────────┘                  │
                                                             ▼
                                              cache: archetype catalog,
                                              price/promo state, JWT
                                              session blacklist
                       ┌──────────────────┐
                       │ Spaces 1 TB      │  $25/mo
                       └──────────────────┘
```

### Pricing

| Item | Cost (USD) | Why |
| --- | --- | --- |
| 2× Droplet `s-2vcpu-4gb` | $48 | 4 vCPUs total; runs nginx + replicas of frontend/backend |
| DO Load Balancer | $12 | terminates TLS, health checks |
| Managed MySQL production w/ standby | $120 | RAM bump for hot index, async replica |
| Managed Valkey 1 GB | $30 | hot cache (see below) |
| Spaces 1 TB | $25 | over the 250 GB tier |
| Bandwidth overage | ~$50 | egress > 1 TB/mo @ $0.01/GB |
| **Total** | **≈ $285 / mo** | + Cloudflare free, + DO Monitoring free |

### Capacity check
- 2 hosts × 2 backend × 2 workers = 8 uvicorn workers ≈ 1,200 RPS at
  "average mix" ⇒ 1k QPS achievable with 17% spare.
- Valkey absorbs reads of `archetype catalog`, price state, and
  rate-limit counters — eliminates ~60% of trivial DB reads.

### Caching strategy

| Key | TTL | Source of truth |
| --- | --- | --- |
| `archetypes:list` | 10 min | `content/cells.py` LRU + Valkey across instances |
| `archetypes:detail:{cell}` | 10 min | same |
| `payment:price` | 30 s | `_current_price()` |
| `careers:for_cell:{cell}` | 10 min | `careers.py` LRU |
| `ratelimit:{ip}:{minute}` | 60 s | counter |

### Operational
- **Sticky sessions.** Only `/api/v3/payment/razorpay/*` needs
  stickiness (the same instance issues + verifies the Order). DO LB
  sticky cookie on path prefix `/api/v3/payment/`.
- **DR.** Managed MySQL standby gives RTO ~5 min, RPO ~30s.
- **Migrations.** Use Alembic (Roadmap 1.3); run as a one-shot job
  before rolling new code.

---

## 4. Tier 3 "Scale" — up to 10,000 QPS, ~1M daily completions

**Goal:** top-100 India web property; multi-region; no single point
of failure; sub-100ms p95 globally.

### Architecture

```
                        Cloudflare Enterprise (paid)
                            │ TLS + DDoS + WAF + image resize
                            ▼
                    ┌──────────────────┐
                    │ Global LB (DO)   │   3 regions: BLR1 / SGP1 / FRA1
                    │ Multi-region HA  │
                    └──┬───────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   ┌────────┐    ┌────────┐    ┌────────┐
   │ DOKS   │    │ DOKS   │    │ DOKS   │      Kubernetes managed clusters
   │ BLR1   │    │ SGP1   │    │ FRA1   │      one cluster per region
   │ active │    │ active │    │ passive│
   │ 6×4vCPU│    │ 6×4vCPU│    │ 6×4vCPU│
   │ 8GB    │    │ 8GB    │    │ 8GB    │
   └────┬───┘    └────┬───┘    └────┬───┘
        │             │             │
        ▼             ▼             ▼
   each cluster runs:
     - Next.js Deployment ×8 (HPA 4–16 by CPU)
     - FastAPI Deployment ×8 (HPA 4–24 by CPU)
     - Valkey StatefulSet, 3 nodes, sentinel
     - Nginx ingress controller w/ rate-limit annotations
     - Prometheus + Grafana

   shared:
     - DO Managed MySQL production-xl-2tb / 8 vCPU / 32 GB / read-replica per region
     - DO Spaces 5 TB w/ CDN
     - DO Container Registry
```

### Sizing (per region)

| Service | Replicas | Per-pod | Total per region |
| --- | --- | --- | --- |
| FastAPI | 8 (HPA 4–24) | 0.5 vCPU / 512 MB / 2 uvicorn workers | 16–48 workers |
| Next.js | 8 (HPA 4–16) | 0.5 vCPU / 512 MB | sufficient |
| Valkey | 3 | 1 vCPU / 2 GB | failover-tolerant cache |

48 backend workers × ~150 RPS each = ~7,200 RPS BLR1 alone; add 50%
from SGP1 active = ~10,800 RPS — meets 10k-QPS target with 8% spare.

### Pricing

| Item | Cost (USD) |
| --- | --- |
| DOKS control plane | $0 (free) |
| Worker nodes — BLR1 (4 vCPU/8 GB × 6) | $384 |
| Worker nodes — SGP1 (× 6) | $384 |
| Worker nodes — FRA1 (× 6, passive) | $384 |
| Managed MySQL production-xl 8vCPU/32GB/200GB w/ standby | $570 |
| Read-replicas × 2 | $1,140 |
| Managed Valkey 4GB w/ standby | $90 |
| Global LB | $36 |
| Spaces 5 TB + CDN | $50 |
| Bandwidth overage (~30 TB/mo) | $300 |
| Cloudflare Enterprise | ~$2,000+ |
| Container Registry | $5 |
| **DO subtotal** | **≈ $3,343 / mo** |
| **All-in (with CF Ent.)** | **≈ $5,300+ / mo** |

### Operational
- **CI/CD.** GitHub Actions builds Docker image → DO Container
  Registry → `kubectl set image` rolling update.
- **Migrations.** Alembic + a Kubernetes Job that runs before new
  pods are healthy.
- **Observability.** DO Monitoring (free) + Prometheus / Grafana in
  cluster + Loki for logs.
- **Region failover.** Global LB pulls BLR1 out on health-check fail;
  SGP1 absorbs traffic.

---

## 5. Cost ladder summary

| Tier | Daily completions | QPS peak | Monthly $ | Time-to-set-up |
| --- | --- | --- | --- | --- |
| Bootstrap | 500 | 10 | **≤ $20** | ~30 min |
| Launch | 5,000 | 100 | $34 | ~2 hours |
| Growth | 100,000 | 1,000 | $285 | ~1 day |
| Scale | 1,000,000 | 10,000 | $3,343 (DO) + $2,000+ (CF) | ~1 week + 2 weeks soak |

Pricing source: [DigitalOcean public pricing](https://www.digitalocean.com/pricing).
Treat as planning input, not a quote.

---

## 6. Pre-launch checklist (any tier)

- [ ] `env/prod.env` populated, **never** committed (it's gitignored)
- [ ] `RAZORPAY_KEY_ID` is `rzp_live_*`, webhook secret rotated
- [ ] `JWT_SECRET` is a long random string, **not** the dev default
- [ ] `OAUTH_STATE_SECRET` set
- [ ] CORS allowlist on `FRONTEND_URL` only (no `*`)
- [ ] DO Spaces public-read policy on `*.pdf` folder only
- [ ] Cloudflare cache rules: `/api/*` bypass, `/static/*` cache 1h,
      `/api/og/*` cache 5m at edge
- [ ] DigitalOcean Monitoring alerts on CPU>80% / RAM>85% / 5xx>1%
- [ ] Razorpay sandbox smoke test passes
      (`python -m scripts.razorpay_sandbox_smoke`)
- [ ] Backend pytest + frontend Vitest + Playwright e2e all green in CI
- [ ] Lighthouse CI accessibility ≥ 0.9 (error)
- [ ] DPDPA / privacy email ticket queue set up
- [ ] `/var/MindPrism/prod/logs/` writable + nightly archive cron set
