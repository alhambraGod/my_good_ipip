# MindPrism — DigitalOcean Deployment

> Three sized recipes (100 / 1000 / 10000 QPS) on DigitalOcean. Pricing
> is from [digitalocean.com/pricing](https://www.digitalocean.com/pricing)
> as of May 2026; verify before you sign POs.

---

## 0. Capacity model — what does 1 QPS mean?

MindPrism's hot endpoints have very different costs:

| Endpoint | Type | Hot path | DB cost | Latency budget |
| --- | --- | --- | --- | --- |
| `GET /` (landing) | Next ISR HTML | static asset | 0 | ≤ 100ms TTFB |
| `GET /archetypes` (+ `[cell]`) | Next ISR | static asset (10-min revalidate) | 0 | ≤ 100ms TTFB |
| `GET /api/v3/archetypes(/...)` | FastAPI read | `cells.json` LRU cache | 0 | ≤ 30ms |
| `GET /api/v3/payment/price` | FastAPI read | 1 row count | 1 SELECT | ≤ 30ms |
| `GET /api/v3/assessment/demographic` | FastAPI read | static py | 0 | ≤ 20ms |
| `POST /api/v3/assessment/start` | FastAPI write | 1 INSERT | 1 INSERT | ≤ 80ms |
| `POST /api/v3/assessment/submit` | FastAPI write + score | scoring math (CPU-bound, ~5–15ms) | 1 UPDATE + 1 INSERT (ShortLink) | ≤ 200ms |
| `GET /api/v3/assessment/{id}/results` | FastAPI read | 1 row + cell content from cache | 1 SELECT | ≤ 50ms |
| `POST /api/v3/payment/razorpay/order` | FastAPI write + outbound HTTPS | Razorpay API call (300–800ms upstream) | 1 UPDATE | ≤ 1s |
| `POST /api/v3/payment/razorpay/verify` | FastAPI write | HMAC verify | 1 UPDATE | ≤ 50ms |
| `POST /api/v3/payment/webhook/razorpay` | FastAPI write | HMAC verify | 1 UPDATE | ≤ 50ms |
| `GET /api/v3/report/{id}` | FastAPI read | 1 row + cell + 5+ careers | 1 SELECT | ≤ 100ms |
| `GET /s/{code}` | FastAPI read + 302 | 1 SELECT + 1 UPDATE (clicks++) | 2 ops | ≤ 30ms |
| `GET /api/og/[id]` | Next nodejs runtime, fetch backend | 1 backend GET | 1 SELECT (via API) | ≤ 600ms (LCP-OK) |

For sizing we assume the **average request mix** at peak:

```
landing/archetypes (CDN + ISR)   60%   ← essentially free for backend
quiz reads (questions, milestone) 20%  ← p95 < 30ms backend
quiz writes (start + submit)     10%   ← p95 < 200ms backend
paywall + report                  8%   ← p95 < 100ms backend (Razorpay async)
share + OG                        2%   ← p95 < 600ms (image) or < 30ms (short)
```

A single FastAPI worker on a 1 vCPU / 1 GiB Droplet sustains ~150 RPS
of "average mix" traffic before p99 latency degrades. Postgres on
managed DO costs more (we model it explicitly).

---

## 1. Tier "Launch" — up to 100 QPS, ≤ 5,000 daily completions

**Goal:** beta launch / early-bird first 1,000 paid users. Single-AZ
acceptable; we manage incident risk via easy rollback.

### Architecture

```
                    Cloudflare CDN (free)
                            │
                            ▼
              ┌────────────────────────┐
              │  App Platform: Next.js │  $12/mo (basic-xxs, 0.5 vCPU / 512 MB, 1 instance)
              │  build = next build    │
              │  serves /, /test,...   │
              └──────────┬─────────────┘
                         │ same VPC
                         ▼
              ┌────────────────────────┐
              │  App Platform: FastAPI │  $12/mo (basic-xxs, 0.5 vCPU / 512 MB, 1 instance)
              │  uvicorn --workers 2   │
              └──────────┬─────────────┘
                         │ private VPC link
                         ▼
              ┌────────────────────────┐
              │  Managed Postgres      │  $15/mo (1 GB RAM / 1 vCPU / 10 GB disk)
              │  db-s-1vcpu-1gb        │
              └────────────────────────┘
              ┌────────────────────────┐
              │  Spaces (S3-compat)    │  $5/mo (250 GB + 1 TB transfer)
              │  PDFs + assets         │
              └────────────────────────┘
```

### Pricing & monthly bill

| Item | Cost | Notes |
| --- | --- | --- |
| App Platform — frontend `basic-xxs` | $12 | "App Platform" pricing tier |
| App Platform — backend `basic-xxs` | $12 | same |
| Managed Postgres `db-s-1vcpu-1gb` | $15 | with daily backups |
| Spaces 250 GB | $5 | for PDFs + OG cards if cached |
| Bandwidth | included | App Platform 100 GB / mo egress free |
| Domain + DNS | free | DO DNS is free |
| **Total** | **≈ $44 / mo** | Cloudflare in front for free CDN + DDoS |

### Capacity check
- Frontend ISR + Cloudflare → effectively unlimited static traffic.
- Backend `basic-xxs` runs 2 uvicorn workers; ~150 RPS average mix
  before saturation. 100 QPS comfortable, p99 < 250ms.
- Postgres 1 vCPU sustains ~600 simple writes/sec — > 30× headroom.

### Operational
- **No autoscaling.** App Platform pin to 1 instance; if you need to
  bounce, "Force redeploy" works zero-downtime via blue/green.
- **Backups.** Managed PG includes daily backups, 7-day retention.
- **Observability.** App Platform has request logs (free); add
  DigitalOcean Monitoring (free for Droplets, included for App
  Platform) for CPU/mem/runtime alerts.
- **Razorpay webhook.** App Platform exposes a stable HTTPS URL
  (e.g. `https://api.mindprism.in.ondigitalocean.app`); use that in
  the dashboard, no ngrok needed.

---

## 2. Tier "Growth" — up to 1,000 QPS, ~100k daily completions

**Goal:** post-launch organic + WhatsApp viral; multi-instance, single
region (BLR1) but horizontally scalable.

### Architecture

```
                       Cloudflare CDN
                             │
                             ▼
                    ┌────────────────┐
                    │ Load Balancer  │  $12/mo (Global LB — Mumbai + Bangalore + Singapore HA)
                    └───────┬────────┘
                            │
          ┌─────────────────┼─────────────────┐
          ▼                                   ▼
┌─────────────────────┐               ┌─────────────────────┐
│ App Platform        │               │ App Platform        │
│ frontend × 3        │               │ backend × 3         │
│ basic-s             │               │ basic-s             │
│ 1 vCPU / 1 GB each  │               │ 1 vCPU / 1 GB each  │
│ ($25 × 3 = $75/mo)  │               │ ($25 × 3 = $75/mo)  │
└─────────────────────┘               └──────────┬──────────┘
                                                 │
                                  ┌──────────────┼──────────────┐
                                  ▼                             ▼
                       ┌──────────────────┐          ┌──────────────────┐
                       │ Managed Postgres │          │ Managed Valkey   │
                       │ Production tier  │          │ (Redis-compat)   │
                       │ 4 GB / 2 vCPU /  │          │ 1 GB / 1 vCPU    │
                       │ 38 GB / standby  │          │ ($30/mo)         │
                       │ ($120/mo)        │          └──────────────────┘
                       └──────────────────┘                  │
                                                             │
                                                             ▼
                                              cache: archetype catalog,
                                              price/promo state, JWT
                                              session blacklist
                       ┌──────────────────┐
                       │ Spaces 1 TB      │  $25/mo
                       │ PDFs + OG cards  │
                       └──────────────────┘
```

### Pricing & monthly bill

| Item | Cost | Why |
| --- | --- | --- |
| Frontend × 3 `basic-s` | $75 | $25/mo per instance |
| Backend × 3 `basic-s` | $75 | each runs uvicorn `--workers 2`; total 6 workers |
| Load Balancer | $12 | terminates TLS, health checks, sticky for `/payment` |
| Managed Postgres production w/ standby | $120 | RAM bump for hot index, async replica |
| Managed Valkey 1 GB | $30 | hot cache (see below) |
| Spaces 1 TB | $25 | over the 250 GB tier |
| Bandwidth overage | ~$50 | if egress > 1 TB/mo at $0.01/GB |
| **Total** | **≈ $387 / mo** | + Cloudflare free, + DO Monitoring free |

### Capacity check
- 3 backend instances × 2 workers = 6 concurrent uvicorn workers
  ≈ 900 RPS at "average mix" ⇒ 1,000 QPS achievable with 10% spare.
- Postgres 4 GB / 2 vCPU sustains ~5k simple ops/sec, ~3k mixed → 5×
  headroom over our 1k QPS target.
- Valkey absorbs reads of `archetype catalog` (24 small JSON), price
  state (1 row count), and rate-limit counters — eliminates ~60% of
  trivial DB reads.

### Caching strategy

| Key | TTL | Source of truth |
| --- | --- | --- |
| `archetypes:list` | 10 min | `content/cells.py` LRU + Valkey across instances |
| `archetypes:detail:{cell}` | 10 min | same |
| `payment:price` | 30 s | `_current_price()` |
| `careers:for_cell:{cell}` | 10 min | `careers.py` LRU |
| `ratelimit:{ip}:{minute}` | 60 s | counter |

### Operational
- **Autoscale.** App Platform supports horizontal autoscale by
  CPU%; configure `minInstances=2, maxInstances=6, cpuThreshold=60`
  per service.
- **Sticky sessions.** Only the `/payment` Razorpay flow needs
  stickiness (the same instance issues + verifies the Order). LB
  sticky-cookie on path prefix `/api/v3/payment/` for 5 min.
- **Background jobs.** None at this tier — Razorpay webhook arrives
  asynchronously to whichever instance the LB picks.
- **DR.** Managed PG standby gives RTO ~5 min, RPO ~30s.
- **Migrations.** Use Alembic (Roadmap 1.3); deploy migrations as a
  one-shot job before rolling new code.

---

## 3. Tier "Scale" — up to 10,000 QPS, ~1M daily completions

**Goal:** top-100 India web property; multi-region; no single point
of failure; sub-100 ms p95 globally.

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
   │ DOKS    │    │ DOKS    │    │ DOKS    │      Kubernetes managed clusters
   │ BLR1    │    │ SGP1    │    │ FRA1    │      one cluster per region
   │ (active)│    │ (active)│    │ (passive)│
   │         │    │         │    │ failover │
   │  3-node │    │  3-node │    │  3-node │
   │  4vcpu  │    │  4vcpu  │    │  4vcpu  │
   │  8GB ×N │    │  8GB ×N │    │  8GB ×N │
   └────┬───┘    └────┬───┘    └────┬───┘
        │             │             │
        ▼             ▼             ▼
   each cluster runs:
     - Next.js frontend  Deployment ×8  (HPA 4–16 by CPU)
     - FastAPI backend   Deployment ×8  (HPA 4–24 by CPU)
     - Valkey (StatefulSet, 3 nodes, sentinel)
     - Nginx ingress controller w/ ratelimit annotations
     - Prometheus / Grafana (DigitalOcean Monitoring add-on)

   shared:
     - DO Managed Postgres production-xl-2tb / 8 vCPU / 32 GB / read-replica per region
     - DO Spaces 5 TB w/ CDN
     - DO Container Registry (free up to 1 repo, $5/mo for more)
```

### Sizing (per region, BLR1 as primary)

| Service | Replicas | Per-pod | Total per region |
| --- | --- | --- | --- |
| FastAPI | 8 (HPA up to 24) | 0.5 vCPU / 512 MB / 2 uvicorn workers | 16 workers minimum, 48 max |
| Next.js | 8 (HPA up to 16) | 0.5 vCPU / 512 MB | sufficient for ISR + dynamic |
| Valkey | 3 | 1 vCPU / 2 GB | failover-tolerant cache |

48 backend workers × ~150 RPS each = ~7,200 RPS BLR1 alone; add 50% from
SGP1 active = ~10,800 RPS — meets 10k-QPS target with 8% spare. FRA1
stays warm for failover.

### Pricing & monthly bill

| Item | Cost (USD) | Notes |
| --- | --- | --- |
| DOKS control plane | $0 | Free in DO Kubernetes |
| Worker nodes — BLR1 (4 vCPU / 8 GB × 6) | $384 | $64/mo each (`s-4vcpu-8gb`) |
| Worker nodes — SGP1 (× 6) | $384 | active |
| Worker nodes — FRA1 (× 6) | $384 | passive (or use spot/fewer if budget tight) |
| Managed Postgres production-xl 8 vCPU / 32 GB / 200 GB / standby | $570 | "production xl" tier (DO public price) |
| Read-replicas × 2 (SGP, FRA) | $570 × 2 | matches primary spec |
| Managed Valkey 4 GB w/ standby | $90 | per-region; or run in-cluster (already counted) |
| Global LB | $36 | 3-region |
| Spaces 5 TB + CDN | $50 | $5 base + overage at $0.02/GB |
| Bandwidth overage | $300 | egress estimated at 30 TB/mo |
| Cloudflare Enterprise | varies | typically ~$2,000+/mo for low end |
| Container Registry | $5 | private images |
| **DO infra subtotal** | **≈ $3,243 / mo** | excludes Cloudflare Enterprise |
| **All-in (with CF Ent.)** | **≈ $5,000–6,000 / mo** | |

### Capacity check
- Active-active BLR1 + SGP1: ~10,800 RPS combined backend capacity.
- Postgres 8 vCPU / 32 GB at primary: ~30k mixed ops/sec. The 10k-QPS
  number in this tier is **HTTP request rate**; backend → DB ratio is
  typically 1:1 for writes and 0.4:1 for reads (Valkey absorbs reads),
  so DB load ≈ 6k ops/sec — 5× headroom.
- Read replicas serve every `GET /api/v3/{archetypes|payment/price|assessment/.../results|report/...}`.

### Operational
- **CI / CD.** GitHub Actions builds Docker image, pushes to DO
  Container Registry, `kubectl set image` rolling update. Argo CD
  optional.
- **Migrations.** Alembic + a Kubernetes Job that runs before the
  new pods are healthy.
- **Observability.**
  - DigitalOcean Monitoring (free, included): CPU/mem/disk/network
  - Prometheus + Grafana inside cluster: app metrics
    (`fastapi-instrumentator` exporters), Razorpay webhook receipt
    counters, payment confirmation latency histograms.
  - Loki / Promtail or ship to Logtail for log aggregation.
  - SLO dashboard: `payment_success_p95`, `submit_p95`,
    `landing_lcp_p95`.
- **Incident response.**
  - Razorpay outage: backend `/razorpay/order` retries with backoff;
    UI degrades to "try again later" toast.
  - Postgres primary failover: Managed PG promotes standby in ~30s.
  - Region failover: Global LB pulls BLR1 out on health-check fail;
    SGP1 absorbs traffic; tail latency rises ~30%.
- **Cost control.**
  - Use spot worker nodes for FRA1 passive (40% cheaper).
  - Spaces lifecycle: PDFs older than 90 days → cold tier.
  - Cloudflare cache aggressively for `/`, `/archetypes`, `/api/og/...`.

---

## 4. Pre-launch checklist (any tier)

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
- [ ] Backend pytest + frontend Vitest + Playwright e2e all green in
      CI
- [ ] Lighthouse CI accessibility ≥ 0.9 (error)
- [ ] DPDPA / privacy email ticket queue set up (email forward to
      ops mailbox)

## 5. Cost ladder summary

| Tier | Daily completions | QPS peak | Monthly $ | Time-to-set-up |
| --- | --- | --- | --- | --- |
| Launch | 5,000 | 100 | $44 | ~2 hours |
| Growth | 100,000 | 1,000 | $387 | ~1 day |
| Scale | 1,000,000 | 10,000 | $3,243 (DO) + $2,000+ (CF Ent.) | ~1 week + 2 weeks of soak tests |

> Pricing source: [DigitalOcean public pricing](https://www.digitalocean.com/pricing).
> Treat as a planning input, not a quote — confirm with DO sales before
> production commit, especially Cloudflare Enterprise.
