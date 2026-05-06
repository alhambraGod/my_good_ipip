# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**MindPrism** (formerly MindIQ / CareerDNA, Apr 2026) — Holland RIASEC + Big Five (IPIP-NEO) hybrid personality + career assessment, India-tuned. FastAPI backend + Next.js 16 frontend.

## Documentation index

Operator + design docs live under `docs/` (English in `docs/en/`, 中文在 `docs/zh/`).
Start with [`docs/README.md`](docs/README.md) for the bilingual index.

Read these BEFORE making non-obvious changes:

**Living docs (always current):**

| File | When to read |
| --- | --- |
| [`docs/en/product.md`](docs/en/product.md) | What MindPrism is, who it's for, the user journey, free vs. paid scope, archetype catalog. |
| [`docs/en/architecture.md`](docs/en/architecture.md) | System topology, repo layout, data model, payment + auth + i18n + testing pyramid, decisions ledger. |
| [`docs/en/infrastructure.md`](docs/en/infrastructure.md) | nginx + scale-out: same-host replicas → multi-host → multi-region; logging at scale; common mistakes. |
| [`docs/en/roadmap.md`](docs/en/roadmap.md) | Quarter-by-quarter forward plan + explicit non-goals. |
| [`docs/en/deployment-digitalocean.md`](docs/en/deployment-digitalocean.md) | Sized deploy recipes for 10 / 100 / 1,000 / 10,000 QPS on DigitalOcean (Bootstrap tier ≤ $20/mo). |
| [`docs/en/deployment-docker.md`](docs/en/deployment-docker.md) | Container-by-container deploy: dev (in-container MySQL), prod (host MySQL), native fallback, env reference, backup recipes. |
| [`docs/en/payment-providers.md`](docs/en/payment-providers.md) | India payment landscape research; Razorpay / Cashfree / PayU / UPI Intent integration spec. |
| [`docs/en/runbook-payments.md`](docs/en/runbook-payments.md) | Mock → Razorpay test → live; webhook + smoke + rollback. |
| [`docs/en/ci-cd-setup.md`](docs/en/ci-cd-setup.md) | GitHub Actions: required status checks, LHCI app token, secret list, deploy-staging job sketch. |

**History (point-in-time snapshots, do not edit):**

| File | What it captures |
| --- | --- |
| `docs/superpowers/specs/2026-04-27-careerdna-india-redesign-design.md` | Apr 2026 product spec — referenced by phase plans. |
| `docs/superpowers/plans/2026-04-27-careerdna-phase-1-backend-foundation.md` | Phase 1 implementation plan + completion notes. |
| `docs/superpowers/plans/2026-04-28-careerdna-phase-2-content-library.md` | Phase 2 — Pydantic content schemas + 24 cells + careers. |
| `docs/superpowers/plans/2026-04-28-careerdna-phase-3-api-payment-auth.md` | Phase 3 — v3 API surface, Razorpay, OAuth, share. |
| `docs/superpowers/plans/2026-04-28-careerdna-phase-4-frontend-mvp.md` | Phase 4 — Next.js MVP frontend wiring. |

## Commands

### Start all services
```bash
bash start_all.sh [dev|stage|prod]   # default: dev
```

### Docker (recommended for any deploy ≥ Bootstrap tier)
```bash
sudo bash deploy/start_docker.sh dev          # dev:  nginx + frontend + backend + mysql
sudo bash deploy/start_docker.sh prod         # prod: nginx + frontend + backend (host MySQL)
sudo bash deploy/scale.sh    prod backend=3 frontend=2     # scale replicas
sudo bash deploy/stop_docker.sh prod          # graceful stop
```

### Native (no Docker — laptops + small VMs)
```bash
bash deploy/start_native.sh dev               # SQLite fallback if MySQL absent
bash deploy/start_native.sh prod              # requires DATABASE_URL pointing at host MySQL
```

### Backend only (legacy, kept for compat)
```bash
bash backend/deploy_backend.sh [dev|stage|prod]
# Or manually:
conda activate my_good_ipip
cd backend && uvicorn main:app --host 0.0.0.0 --port 3001 --reload
```

### Frontend only (legacy, kept for compat)
```bash
bash frontend/deploy_frontend.sh [dev|stage|prod]
# Or manually:
cd frontend && npm install && npm run dev
```

### Host-level installs (run once on each host)
```bash
sudo bash deploy/install_mysql_prod.sh        # MySQL 8 + utf8mb4 + db user
sudo bash deploy/install_nginx.sh prod        # native nginx (skip if using Docker)
sudo bash deploy/install_letsencrypt.sh DOMAIN  # TLS via certbot --nginx
```

### Frontend lint
```bash
cd frontend && npm run lint
```

### Frontend production build
```bash
cd frontend && npm run build && npm run start
```

### Tests

Backend (pytest + coverage, in-memory SQLite). Coverage threshold: **80%**, currently **83.3%**:
```bash
conda activate my_good_ipip
cd backend && pytest -q                    # default: with coverage + threshold
cd backend && pytest --no-cov -q           # faster inner-loop, no coverage
cd backend && pytest --cov-report=html     # also write htmlcov/index.html
```

Frontend (Vitest, happy-dom):
```bash
cd frontend && npm test           # run once (45 tests across 8 files)
cd frontend && npm run test:watch # watch mode
cd frontend && npm run test:ui    # browser UI
```

Frontend E2E (Playwright). Smoke is **backend-free** (uses an unreachable
mock URL); a11y suite checks WCAG 2.1 AA via axe-core:
```bash
cd frontend && npm run test:e2e        # headless: smoke (6) + a11y (4)
cd frontend && npm run test:e2e:ui     # Playwright UI runner
```

For full data-flow e2e (will need backend up):
```bash
# in another shell: bash start_all.sh dev
cd frontend && E2E_NO_WEBSERVER=1 \
  E2E_BASE_URL=http://localhost:3000 \
  E2E_API_URL=http://localhost:3001 \
  npm run test:e2e
```

Lighthouse / perf budget (Lighthouse CI; spawns its own server):
```bash
cd frontend && npm run lighthouse           # build + start + collect + assert
cd frontend && npm run lighthouse:collect   # collect only, against running server
```

Razorpay sandbox smoke (verifies test-mode credentials + signing):
```bash
PAYMENT_MODE=razorpay \
RAZORPAY_KEY_ID=rzp_test_xxx \
RAZORPAY_KEY_SECRET=xxxxx \
python -m scripts.razorpay_sandbox_smoke
# from inside backend/, after `conda activate my_good_ipip`
```

## Environment System

Three environments: `dev`, `stage`, `prod`. Config files in `env/{dev,stage,prod}.env`.

- **dev**: hot reload enabled (uvicorn `--reload`, `next dev`)
- **stage/prod**: no hot reload; backend runs with `--workers 2`, frontend uses `next build && next start`

Deploy scripts auto-generate `backend/.env` and `frontend/.env.local` from the central env file.

Key vars (full list in `.env.example`):

| Var | Purpose |
| --- | --- |
| `APP_ENV` | `dev` / `stage` / `prod` |
| `DATABASE_URL` | SQLAlchemy URL (sqlite for dev/CI; `mysql+pymysql://...` for stage/prod) |
| `LOG_ROOT` | Log root, default `/var/MindPrism` |
| `LOG_RETENTION_DAYS` | History archive retention (default 30) |
| `PAYMENT_MODE` | `mock` (dev default) / `razorpay` |
| `RAZORPAY_KEY_ID` / `_SECRET` / `_WEBHOOK_SECRET` | Razorpay creds — see RUNBOOK |
| `FRONTEND_URL` | Browser-facing site root (CORS, callback URLs) |
| `API_PUBLIC_URL` | Browser-facing API root (used in `/s/{code}` short links) |
| `NEXT_PUBLIC_SITE_URL` | Frontend self-URL for OG metadata + sitemap |
| `NEXT_PUBLIC_API_URL` | Frontend → backend base URL |
| `JWT_SECRET` | JWT signing key — **must override in prod** |
| `GUNICORN_WORKERS` | Backend worker count for `gunicorn` (Docker prod default 2) |

## Architecture

### Backend (`backend/`)

FastAPI app at `main.py`. Config via Pydantic Settings in `config.py` (reads `.env`).

**Data flow (v3):**
demographic Q1–5 → POST `/start` → 40 dynamic Qs (24 RIASEC + 16 IPIP/interest) →
POST `/submit` → scoring (RIASEC + OCEAN + Holland code + archetype cell) →
free results → optional Razorpay → paid report (cell deep dive + careers).

- **Routers** (`routers/`):
  - v1 (legacy): `assessment`, `payment`, `report` — kept for compat
  - v3: `assessment_v3`, `payment_v3`, `report_v3`, `archetypes`, `share`, `auth`
- **Services**:
  - `services/scoring/` — `riasec`, `ocean`, `holland_code`, `archetype` (MAST trigger)
  - `services/payment/` — `base.PaymentDriver` Protocol; `MockDriver` / `RazorpayDriver` / `CashfreeDriver` / `PayUDriver` / `UPIIntentDriver`; multi-driver registry in `factory.py` selected via `PAYMENT_DRIVERS_ENABLED` + `PAYMENT_DEFAULT_DRIVER` (back-compat `PAYMENT_MODE`)
  - `services/oauth_service.py` — Google / Facebook / WhatsApp / Twitter / Telegram
  - `services/milestone_copy.py` — Q10/20/30/40 copy pools, `lang=en/hi`
  - `services/jwt_service.py` — `get_current_user` Bearer / `?token=` dependency
- **Content**: `content/cells/*.json` (24 archetypes), `content/careers.json` (~78 careers); Pydantic-validated by `content/models.py`, loaded via `content/cells.py` + `content/careers.py`.
- **Database**: SQLAlchemy 2.0 + SQLite, `StaticPool` for `:memory:` to share state across `TestClient` threads. Models: `Assessment`, `UserProfile`, `ShortLink`. New columns are added idempotently in `_ensure_assessment_columns()` on startup — no Alembic.
- **Questions**: 5 fixed demographic, 24 hand-curated RIASEC (4 per type), 16 dynamic IPIP/interest selected by demographic tags + seed.

API docs auto-generated at `http://localhost:3001/docs`.

### Frontend (`frontend/`)

Next.js 16.2.2 + React 19 + TypeScript + Tailwind CSS 4 + Framer Motion 12.

- **API clients**:
  - `lib/v3-api.ts` — typed v3 fetch wrappers (questions, payment intent + Razorpay, archetypes, milestone with lang)
  - `lib/api.ts` — legacy v1 client + auth helpers (kept for compat)
- **i18n**: `lib/i18n/strings.ts` (`en` / `hi`) + `LangProvider` (useSyncExternalStore on localStorage). `<LangToggle />` in the header.
- **State hooks**: `useAssessmentProgress` (localStorage-backed quiz state, survives refresh), `useDigitKey` (1–5 keyboard shortcut for Likert).
- **Routes**:
  - Public: `/`, `/archetypes`, `/archetypes/[cell]`, `/auth/*/callback`
  - Quiz: `/test`
  - Results / paywall: `/results/[id]`, `/payment`, `/payment/success`, `/report/[id]`
  - Dynamic OG: `/api/og/[id]` (Edge ImageResponse), `/sitemap.xml`, `/robots.txt`
- **Razorpay Checkout SDK**: `lib/razorpay.ts` lazily injects `checkout.razorpay.com/v1/checkout.js`; `<RazorpayCheckoutButton />` opens an in-page modal, calls `/razorpay/verify`, then `router.push('/payment/success')`. Falls back to a redirect URL when `PAYMENT_MODE=mock`.
- **Auth modal**: `<UnlockAuthModal />` — Google / Facebook / WhatsApp + guest-pay; `lib/oauth-return.ts` round-trips the post-OAuth path.
- **Reports page**: `<TableOfContents />` (sticky desktop sidebar + mobile chip rail with IntersectionObserver scroll-spy).
- **Import alias**: `@/*` maps to project root.

### Big Five Dimensions

Dimension keys used throughout both frontend and backend: `openness`, `conscientiousness`, `extraversion`, `agreeableness`, `neuroticism`.

## Important Notes

- Next.js 16.2.2 has breaking changes from earlier versions (e.g. `set-state-in-effect` lint rule under React 19). Read `node_modules/next/dist/docs/` before non-trivial frontend changes.
- **Payment provider registry** (multi-driver): `PAYMENT_DRIVERS_ENABLED=razorpay,upi,cashfree,mock` lights up all four for the UI picker. `PAYMENT_DEFAULT_DRIVER` (or back-compat `PAYMENT_MODE`) is the recommended one. See [`docs/en/payment-providers.md`](docs/en/payment-providers.md) for the per-driver integration spec.
- **dev vs prod paywall**: `ALLOW_FREE_REPORT=true` (dev default) makes `/api/v3/report/{id}` return the deep report unpaid with `is_preview=true` so the UI can watermark. `false` (prod default) returns 402 — strictly pay-to-read.
- **GET `/api/v3/payment/providers`** lists the enabled drivers + their UI metadata (label, description, recommended). Frontend `<PaymentMethodPicker />` reads it.
- No Alembic migrations yet — `init_db()` creates tables, then `_ensure_columns()` / `_ensure_indexes()` add new columns idempotently on startup. Both **SQLite** (dev/CI) and **MySQL** (stage/prod) are supported via SQLAlchemy URL switching.
- **Logs** land in `/var/MindPrism/<env>/logs/{app,access,error}.log`, rotate nightly into `logs/history/<file>.YYYY-MM-DD`. Configured by `services/logging_setup.py`.
- Test baselines to match before merging:
  - **Backend pytest**: 197 passing, **coverage ≥ 80%** (`pytest.ini` enforces `--cov-fail-under=80`; current: 83.3%). Coverage omits OAuth/legacy/external-IO modules — see `.coveragerc`.
  - **Frontend Vitest**: 45 passing across 8 files (hooks + i18n + components + landing client).
  - **Playwright e2e smoke**: 6 passing (`frontend/e2e/smoke.spec.ts`) — backend-free.
  - **Playwright a11y (axe)**: 4 passing (`frontend/e2e/a11y.spec.ts`), zero WCAG 2.1 AA violations on landing / archetypes / 404 / Hindi-toggled landing.
  - **Lighthouse CI**: `npm run lighthouse` enforces categories — accessibility ≥ 0.9 (error), best-practices ≥ 0.85 / SEO ≥ 0.9 / performance ≥ 0.7 (warn). See `lighthouserc.cjs`.
- The legacy `services/scoring.py` was renamed to `services/scoring_legacy.py`; `questions/question_bank.py` is now a deprecation shim around the modular loaders. Both will be deleted in Phase 5.
