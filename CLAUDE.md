# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CareerDNA India (codename MindIQ) — Holland RIASEC + Big Five (IPIP-NEO) hybrid career assessment built for the Indian market. FastAPI backend + Next.js 16 frontend.

## Documentation index

Operator + design docs live under `docs/`. Read these BEFORE making non-obvious changes:

| File | When to read |
| --- | --- |
| [`docs/RUNBOOK_payments.md`](docs/RUNBOOK_payments.md) | Going from `mock` → Razorpay test mode → live; webhook + smoke + rollback. |
| `docs/superpowers/specs/2026-04-27-careerdna-india-redesign-design.md` | Authoritative product spec for the v3 redesign (24 archetypes, 5 + 40 question flow, paywall, sharing, OAuth, payments). |
| `docs/superpowers/plans/2026-04-27-careerdna-phase-1-backend-foundation.md` | Phase 1 — question infra, scoring, archetypes. |
| `docs/superpowers/plans/2026-04-28-careerdna-phase-2-content-library.md` | Phase 2 — Pydantic content schemas + 24 cells + careers. |
| `docs/superpowers/plans/2026-04-28-careerdna-phase-3-api-payment-auth.md` | Phase 3 — v3 API surface, Razorpay, OAuth, share. |
| `docs/superpowers/plans/2026-04-28-careerdna-phase-4-frontend-mvp.md` | Phase 4 — Next.js MVP frontend wiring. |

## Commands

### Start all services
```bash
bash start_all.sh [dev|stage|prod]   # default: dev
```

### Backend only
```bash
bash backend/deploy_backend.sh [dev|stage|prod]
# Or manually:
conda activate my_good_ipip
cd backend && uvicorn main:app --host 0.0.0.0 --port 3001 --reload
```

### Frontend only
```bash
bash frontend/deploy_frontend.sh [dev|stage|prod]
# Or manually:
cd frontend && npm install && npm run dev
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

Backend (pytest, in-memory SQLite):
```bash
conda activate my_good_ipip
cd backend && pytest -q
```

Frontend (Vitest, happy-dom):
```bash
cd frontend && npm test           # run once
cd frontend && npm run test:watch # watch mode
cd frontend && npm run test:ui    # browser UI
```

Frontend E2E (Playwright; needs both servers running):
```bash
# in another shell: bash start_all.sh dev
cd frontend && npm run test:e2e        # headless
cd frontend && npm run test:e2e:ui     # Playwright UI runner
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
| `PAYMENT_MODE` | `mock` (dev default) / `razorpay` |
| `RAZORPAY_KEY_ID` / `_SECRET` / `_WEBHOOK_SECRET` | Razorpay creds — see RUNBOOK |
| `FRONTEND_URL` | Browser-facing site root (CORS, callback URLs) |
| `API_PUBLIC_URL` | Browser-facing API root (used in `/s/{code}` short links) |
| `NEXT_PUBLIC_SITE_URL` | Frontend self-URL for OG metadata + sitemap |
| `NEXT_PUBLIC_API_URL` | Frontend → backend base URL |

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
  - `services/payment/` — `base.PaymentDriver` Protocol; `MockDriver` + `RazorpayDriver` (Order + Checkout SDK + payment-link); factory selects via `PAYMENT_MODE`
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
- `PAYMENT_MODE=mock` bypasses Razorpay (and legacy Stripe) in dev. Set to `razorpay` with real keys for production — see [`docs/RUNBOOK_payments.md`](docs/RUNBOOK_payments.md).
- No Alembic migrations — `init_db()` creates tables, then `_ensure_assessment_columns()` / `_ensure_assessment_indexes()` add new columns idempotently on startup.
- Test counts to match before merging:
  - Backend pytest: **179 passing** at last run (`backend/tests/`)
  - Frontend Vitest: **45 passing** (`frontend/lib/**/__tests__`, `frontend/components/__tests__`, `frontend/app/__tests__`)
  - Playwright e2e: **6 passing** (`frontend/e2e/`) — `npm run test:e2e` self-builds + serves on port 3100 with an unreachable mock backend; for full data flow, set `E2E_NO_WEBSERVER=1 E2E_BASE_URL=http://localhost:3000 E2E_API_URL=http://localhost:3001` and run with `bash start_all.sh dev` already up.
- The legacy `services/scoring.py` was renamed to `services/scoring_legacy.py`; `questions/question_bank.py` is now a deprecation shim around the modular loaders. Both will be deleted in Phase 5.
