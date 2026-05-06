# MindPrism — Architecture

> System design, runtime topology, code layout, and the decisions that
> got us here. Read **product.md** first if you don't know what
> MindPrism does.

```
                ┌──────────────────────────────────────────────┐
                │  Next.js 16 (frontend)                       │
                │  ─────────────────────                       │
                │  • SSR + ISR + Edge OG (`/api/og/[id]`)      │
                │  • RSC for landing/archetypes; client comps  │
                │    for /test, /payment, /results, /report    │
                │  • i18n via useSyncExternalStore + ls        │
                │  • Razorpay JS SDK (in-page modal)           │
                └────────┬─────────────────────────────────────┘
                         │ JSON over HTTPS
              ┌──────────┴──────────────────────┐
              │  FastAPI (backend)              │
              │  ─────────────                  │
              │  • /api/v3/assessment/*         │
              │  • /api/v3/payment/* (mock + Razorpay) │
              │  • /api/v3/report/* (paid-only) │
              │  • /api/v3/archetypes/*         │
              │  • /s/{code} short links + /api/share/{id}/og.png stub │
              │  • /api/auth/* (Google / Facebook / WhatsApp /  │
              │     Twitter / Telegram / email)                 │
              └────────┬────────────────┬───────┘
                       │                │
        ┌──────────────┴──┐   ┌─────────┴─────────────┐
        │ SQLAlchemy 2.0  │   │ Razorpay (Order +     │
        │ + SQLite (dev)  │   │ Checkout SDK + webhook │
        │ + Postgres (prod)│  │  signature)            │
        └─────────────────┘   └────────────────────────┘
```

## 1. Repository layout

```
my_good_ipip/                       (legacy repo name; conda env: my_good_ipip)
│
├── backend/                        FastAPI app
│   ├── main.py                     app factory, router mounting, lifespan
│   ├── config.py                   Pydantic Settings (.env)
│   ├── database.py                 engine, sessions, schema migrations
│   ├── models.py                   Assessment / UserProfile / ShortLink
│   ├── schemas.py                  Pydantic v2 request/response models
│   ├── routers/
│   │   ├── assessment_v3.py        demographic / start / submit / state / results / milestone / attach-profile
│   │   ├── payment_v3.py           price / create-intent / razorpay/order / razorpay/verify / webhook / verify
│   │   ├── report_v3.py            paid-only deep report
│   │   ├── archetypes.py           public list + detail
│   │   ├── share.py                short-link redirect + OG stub
│   │   ├── auth.py                 OAuth (Google/FB/WA/X/TG) + email
│   │   └── assessment.py / payment.py / report.py     # v1 legacy, kept for compat
│   ├── services/
│   │   ├── scoring/                modular: riasec / ocean / holland_code / archetype
│   │   ├── payment/                base.PaymentDriver + Mock + Razorpay + factory
│   │   ├── milestone_copy.py       Q10/20/30/40 pools (en / hi)
│   │   ├── jwt_service.py          token issue + Bearer dependency
│   │   ├── oauth_service.py        provider auth-url + code-exchange
│   │   ├── ai_report.py            (legacy) GPT-4o report writer
│   │   └── pdf_generator.py        WeasyPrint + Jinja2
│   ├── content/
│   │   ├── models.py               Pydantic v2 schemas
│   │   ├── cells.py / careers.py   read-only loaders (LRU + MappingProxyType)
│   │   ├── validators.py           cross-ref invariants
│   │   └── data/
│   │       ├── cells/*.json        24 archetype cells
│   │       └── careers/library.json (~78 careers)
│   ├── questions/
│   │   ├── demographic.py          Q1-5 (fixed)
│   │   ├── holland_riasec.py       60 RIASEC items (loaded from json)
│   │   ├── ipip_neo.py             120 IPIP-NEO items
│   │   ├── interest_pool.py        30+ Hinglish interest items
│   │   ├── riasec_static_24.py     curated 24-item subset (4/type)
│   │   ├── selector.py             L1.5 dynamic 45-question composer
│   │   ├── question_bank.py        deprecation shim → modular loaders
│   │   └── models.py               Question dataclass
│   ├── scripts/
│   │   └── razorpay_sandbox_smoke.py   verify test-mode keys + signing
│   └── tests/                      pytest, in-memory SQLite, ~179 tests
│
├── frontend/                       Next.js 16 + React 19 + Tailwind 4
│   ├── app/
│   │   ├── layout.tsx              metadata, Lang + Toast providers
│   │   ├── page.tsx                landing (server) + _landing-client.tsx
│   │   ├── archetypes/             /archetypes + [cell] (ISR)
│   │   ├── test/page.tsx           45-question flow w/ progress hook + keyboard
│   │   ├── results/[id]/           5-screen scroll + OG metadata
│   │   ├── payment/                Razorpay Checkout button + price strip
│   │   ├── report/[id]/            sticky TOC + deep dive
│   │   ├── auth/*/callback         OAuth return paths
│   │   ├── api/og/[id]/            Edge ImageResponse share card
│   │   ├── sitemap.ts / robots.ts
│   │   ├── not-found.tsx / error.tsx / loading.tsx
│   │   └── __tests__               Vitest
│   ├── components/
│   │   ├── SiteHeader / SiteFooter
│   │   ├── LangToggle              EN / हि toggle
│   │   ├── TableOfContents         scroll-spy via IntersectionObserver
│   │   ├── RazorpayCheckoutButton  loadSDK + open + verify
│   │   ├── UnlockAuthModal         dialog, OAuth providers + guest pay
│   │   ├── Toast                   global ToastProvider + useToast()
│   │   ├── RadarChart              SVG, R/I/A/S/E/C labels + score legend
│   │   └── __tests__               Vitest
│   ├── lib/
│   │   ├── api.ts                  v1 + auth client
│   │   ├── v3-api.ts               typed v3 fetchers
│   │   ├── razorpay.ts             SDK lazy loader
│   │   ├── oauth-return.ts         post-OAuth redirect path stash
│   │   ├── i18n/                   strings.ts + LangContext.tsx
│   │   └── hooks/                  useAssessmentProgress, useDigitKey
│   ├── e2e/                        Playwright (smoke + a11y / axe)
│   ├── playwright.config.ts        webServer, port 3100
│   ├── lighthouserc.cjs            Lighthouse CI
│   ├── vitest.config.ts            happy-dom + Storage polyfill
│   └── package.json                npm scripts: lint, test, test:e2e, lighthouse
│
├── docs/
│   ├── product.md                  user-facing description (this dir)
│   ├── architecture.md             you are here
│   ├── roadmap.md                  what's next
│   ├── deployment-digitalocean.md  100/1000/10000 QPS plans
│   ├── runbook-payments.md         Razorpay test → live operator guide
│   └── superpowers/                phase plans + design spec (history)
│
├── env/                            dev.env / stage.env / prod.env (central source)
├── .env.example                    public template
├── start_all.sh / backend/deploy_backend.sh / frontend/deploy_frontend.sh
├── CLAUDE.md                       index for AI agents
└── .github/workflows/ci.yml        pytest matrix + frontend + e2e + lighthouse
```

## 2. Key data model

### `Assessment` (the central row)

| Column | Purpose |
| --- | --- |
| `id`                       | UUID, primary key |
| `created_at`               | timestamptz |
| `demographic`              | JSON, Q1-5 answers |
| `question_set_version`     | `"v3_45_hybrid"` |
| `question_ids`             | JSON list of IDs (used to allow `/state` resume) |
| `selection_seed`           | per-respondent randomisation seed |
| `answers`                  | JSON map `qid → 1..5` |
| `completed`                | bool |
| `paid`                     | bool |
| `riasec_scores`            | JSON `{R: int, ...}` |
| `ocean_scores`             | JSON `{openness: 0-100, ...}` |
| `ocean_percentiles`        | JSON `{openness: 0-99, ...}` |
| `holland_code`             | 3-letter code, e.g. `"IAC"` |
| `archetype_cell`           | 2-letter cell, e.g. `"IA"` |
| `archetype_label_en`       | denormalised label (cached) |
| `archetype_rarity_pct`     | denormalised rarity (cached) |
| `payment_provider`         | `mock | razorpay | wechat | stripe` |
| `payment_status`           | `pending | confirmed | failed | refunded` |
| `payment_txn_id`           | Razorpay payment-link / order id |
| `payment_amount_inr`       | int |
| `share_code`               | 8-char short-link code |
| `pdf_path`                 | optional, set when WeasyPrint output is staged |
| `report_data`              | JSON cache of the composed report (future) |
| `profile_session_token`    | optional FK to `UserProfile.session_token` (post-login attach) |

Schema migrations: idempotent `_ensure_assessment_columns()` runs at
`init_db()` and adds any new columns to existing rows. No Alembic in
v1; we'll switch to Alembic when we move to managed Postgres in
production.

### `UserProfile`

OAuth identity row, `session_token` indexed for legacy lookup; `email`
unique-indexed. JWT issued at `/api/auth/{provider}/callback`.

### `ShortLink`

`code → assessment_id + canonical_url`, `clicks` counter, `created_at`.
FK with `ON DELETE CASCADE`.

## 3. Question + scoring pipeline

```
                                                    ┌──────────────────────┐
                                                    │ services/scoring/    │
                                                    ├──────────────────────┤
demographic answers (Q1-5)  ─┐                     │ riasec.compute_*     │
                              ▼                     │ ocean.compute_*      │
                       questions/selector.py        │ holland_code.compute │
                       _select_45_questions()       │ archetype.derive     │
                              │                     └────────┬─────────────┘
                              │  RIASEC 24 (static, hand-curated 4/type)
                              │  IPIP/interest 16 (dynamic, demographic-tagged) ──→ raw scores
                              ▼                                                       ▼
                  POST /api/v3/assessment/start  ←—————— resume via /state            │
                              │                                                       │
                              ▼                                                       ▼
                  POST /api/v3/assessment/submit  ──────────► (likert 1..5) ────────► scores → cell + holland_code + MAST trigger
                              │
                              ▼
                  composed `/results` payload  ─►  cells.get_cell_content + careers.get_careers_for_cell
```

- **Determinism.** `selection_seed` (random urlsafe(16) at `/start`)
  drives both selector and milestone copy; same seed → same ordering /
  same encouragements. Useful for debugging, A/B replay, e2e tests.
- **Compatibility.** `services/scoring_legacy.py` and
  `questions/question_bank.py` are deprecation shims — Phase 5 will
  delete them.

## 4. Payment subsystem

### Drivers
`services/payment/` defines the `PaymentDriver` Protocol with three
methods: `create_payment_intent`, `verify_payment`, `verify_webhook_signature`,
plus (Razorpay-only) `create_order` + `verify_checkout_signature`.
Implementations:

| Driver | Used in | Modes |
| --- | --- | --- |
| `MockDriver` | dev / CI | always-confirms; redirects to `/payment/success?mock=true` |
| `RazorpayDriver` | test + prod | Order + Checkout SDK (preferred), payment-link (fallback) |

`get_payment_driver()` picks the driver from `PAYMENT_MODE`.

### Frontend flow (Razorpay-mode)

```
1. POST /api/v3/payment/razorpay/order → { order_id, key_id, amount_paise }
2. lib/razorpay.loadRazorpayCheckout()    → injects checkout.razorpay.com/v1/checkout.js
3. openRazorpayCheckout({ ... handler })  → in-page modal, user pays
4. handler({ order_id, payment_id, sig }) → POST /api/v3/payment/razorpay/verify
5. router.push(/payment/success?...)
6. (independently) Razorpay POSTs payment.captured / order.paid to /webhook/razorpay
   → backend matches by stored payment_txn_id and double-confirms.
```

### Mock flow

`POST /api/v3/payment/razorpay/order` returns `mock_redirect_url`; the
button just sets `window.location.href` to it. `/payment/success`
calls `/verify/{id}` which auto-confirms. Net: dev never blocks on
Razorpay creds.

### Webhook events handled
- `payment_link.paid` (legacy payment-link flow)
- `order.paid`        (Order flow)
- `payment.captured`  (matches via `order_id` or `payment_link_id`)
- Anything else → 200 + `matched: false` (Razorpay otherwise retries).

### Pricing
`promo_active = paid_count < PROMO_MAX_REDEMPTIONS`, default cap 1000.
Promo price ₹49, full price ₹99. Both env-driven.

## 5. Auth subsystem

| Provider | Spec |
| --- | --- |
| Email + password | bcrypt, signup + login |
| Google OAuth | OAuth 2.0 code flow → `/api/auth/google/callback` |
| Facebook | same; `/api/auth/facebook/callback` |
| WhatsApp (Meta) | same; `/api/auth/whatsapp/callback` |
| Twitter (X) | OAuth 2.0 PKCE; `/api/auth/twitter/callback` |
| Telegram | login widget cb (`/api/auth/telegram/callback`) |

JWT bearer issued at every callback. Frontend stashes `auth_url` next
path in `sessionStorage` (`lib/oauth-return.ts`) so post-OAuth lands
back on `/payment` (not `/profile`).

## 6. Frontend rendering modes

| Route | Mode | Why |
| --- | --- | --- |
| `/` | RSC + Client islands | Initial paint must be fast for share-link inbound |
| `/archetypes` | ISR (10 min) | Content-stable, 24 items |
| `/archetypes/[cell]` | ISR (10 min) | Long-tail SEO |
| `/test` | Client | localStorage hooks, keyboard shortcuts, IntersectionObserver |
| `/results/[id]` | Client (data fetch) + server `generateMetadata` | Per-id OG metadata |
| `/api/og/[id]` | Edge `ImageResponse` | Always-fresh share images |
| `/payment`, `/report/[id]` | Client | Razorpay SDK + Bearer auth |
| `/sitemap.xml`, `/robots.txt` | Static (revalidate 10m) | SEO |
| `/api/og/[id]` | nodejs runtime | shares cookies → backend |

## 7. i18n

- `STRINGS = { en, hi }` literal map in `lib/i18n/strings.ts`.
- `LangProvider` uses `useSyncExternalStore` over `localStorage` so the
  current lang survives reloads and never violates React 19's
  `set-state-in-effect` rule.
- `STRINGS["en"]` and `STRINGS["hi"]` are checked for key parity by a
  Vitest test.
- Where the Hindi label exists in content (cell `label_hi`, career
  `name_hi`) the UI prefers it when `lang === "hi"`. Where there is no
  Hindi (e.g. `cell.deep_description_en`) we fall back to English —
  documented in product.md.

## 8. Testing pyramid

| Layer | Tooling | Count | Where it lives |
| --- | --- | --- | --- |
| Backend unit + API | pytest + httpx TestClient + in-memory SQLite + StaticPool | **179** | `backend/tests/` |
| Backend coverage gate | pytest-cov, `--cov-fail-under=85` | **87.2%** measured | `.coveragerc` |
| Frontend unit (hooks + components) | Vitest + happy-dom + RTL | **45** | `frontend/lib/**/__tests__`, `frontend/components/__tests__`, `frontend/app/__tests__` |
| Frontend e2e (smoke) | Playwright + Chromium | **6** | `frontend/e2e/smoke.spec.ts` |
| Frontend a11y | axe-core + Playwright | **4** | `frontend/e2e/a11y.spec.ts`, zero WCAG 2.1 AA violations |
| Lighthouse CI | `@lhci/cli`, autorun | a11y ≥ 0.9 enforced | `frontend/lighthouserc.cjs` |
| Razorpay smoke | live API hitter | manual | `backend/scripts/razorpay_sandbox_smoke.py` |

CI matrix in `.github/workflows/ci.yml` runs: backend × {3.11, 3.12} +
frontend (lint + Vitest + build) + Playwright e2e + Lighthouse CI with
auto PR comments.

## 9. Deployment topology

See **deployment-digitalocean.md** for sized recipes (100 / 1000 /
10000 QPS).

Summary:
- Frontend: stateless Next.js, scales horizontally behind LB.
- Backend: stateless FastAPI behind LB; DB connection pooled.
- DB: Postgres in stage/prod (env says `DATABASE_URL=postgresql+psycopg://`),
  managed (DigitalOcean Managed Postgres or equivalent).
- Cache (future): Redis / Valkey for archetype catalog + price
  endpoint at higher QPS.
- Object storage: Spaces (S3-compat) for generated PDFs.
- Edge / OG: Next.js `/api/og/[id]` runs in node; can move to edge
  later for global low-latency.

## 10. Decisions ledger (so future-me doesn't re-debate)

| Decision | Choice | Rationale | Reversible? |
| --- | --- | --- | --- |
| Single product vs. dual viral funnel | **Single (MindPrism)** with IBTI viral DNA on result page | Lowest engineering cost while keeping virality | yes (v2 can split) |
| 6-type framework | Holland double-letter (24 cells) | Mathematical 24 = 6×4 with hexagon adjacency, matches existing cell content authoring | hard |
| OCEAN role | Personalisation only — not classification | Keep cell logic clean | yes |
| Question structure | 5 dem + 24 RIASEC + 16 IPIP/interest = 45 | Reliable α; clean phase separation | yes |
| Selector | L1.5 dynamic IPIP/interest, RIASEC 24 static | Cross-user comparable RIASEC, demographic-aware IPIP | yes |
| Result page | 5-screen scroll, soft paywall ~6%, 3 share touchpoints | Maximises virality + conversion | yes |
| Login binding | Only at "Unlock" click | Removes friction from quiz + free results browsing | yes |
| Payment | Razorpay personal-KYC v1, in-page Checkout SDK | Auto-confirmation UX, evades company registration delay | hard until business KYC |
| OAuth providers | Email + WhatsApp + Google + Facebook (X / Telegram disabled in v1) | Aligned with Indian usage; X/TG stubbed for ops | yes |
| Visual style | Saffron-green hybrid (Indian flag-inspired) | Scientific + viral + locally rooted | yes |
| i18n | English with Hindi toggle, Devanagari for career names; 4 South-Indian languages deferred | Sweet-spot for v1 launch | yes |
| Frontend framework | Next.js 16 (Turbopack) + React 19 + Tailwind 4 | Server + client + edge in one toolchain; React 19 set-state-in-effect rules adopted | hard |
| Backend framework | FastAPI + SQLAlchemy 2.0 + Pydantic 2 + SQLite (dev) / Postgres (prod) | Type-safe + cheap + scales horizontally | hard |
| Test environment | happy-dom (not jsdom) | Node 25 ships a broken localStorage that hides jsdom's; happy-dom + in-memory polyfill works cleanly | yes |
| Coverage gate | 85% (backend), zero a11y violations (frontend) | Real, achievable bars; raise to 90% / lighthouse perf budget over time | yes |

## 11. Known follow-ups (operational)

- [ ] Migrate dev SQLite → Postgres parity (Docker compose) so
      schema-migration drift is caught earlier.
- [ ] Add Alembic before the first non-additive schema change.
- [ ] Replace v1 `/api/assessment/*` routers with `/api/v3/*` (cutover
      planned in `docs/superpowers/plans/...phase-3...md`).
- [ ] Drop `services/scoring_legacy.py` and `questions/question_bank.py`.
- [ ] Move OG image generation to Edge runtime once Vercel/CF edge
      compatibility is confirmed for ImageResponse with our brand
      gradient.
- [ ] Add WeasyPrint Devanagari font bundle so PDF Hindi names render.
