# MindPrism — Roadmap

> Forward-looking plan, organised by quarter. Cuts apply when a quarter
> moves; the test-baselines column changes only when a feature lands.
>
> Anything marked **Stretch** ships only if the quarter has slack.

---

## Q3 2026 — Live launch ("v1")

**North-star metric:** 1,000 organic completions / 7-day rolling.

| ID | Item | Why | Acceptance |
| --- | --- | --- | --- |
| 1.1 | Razorpay live KYC + ₹49 → ₹99 promo cap monitoring | Without this, ops is fire-fighting | First 100 paid users without manual ops |
| 1.2 | Migrate dev SQLite → Postgres parity (Docker compose) | Catch schema drift before prod | `bash start_all.sh dev` runs Postgres |
| 1.3 | Alembic for non-additive migrations | Today we only do `ADD COLUMN IF NOT EXISTS` | First migration committed |
| 1.4 | Drop `services/scoring_legacy.py` + `questions/question_bank.py` shim | Phase 5 cleanup | All v1 routers + tests deleted; pytest count drops, coverage holds |
| 1.5 | WhatsApp share — pre-approved business templates | Currently uses `wa.me/?text=` which has 200-char limit | Approved Meta template fires when `navigator.share` unavailable |
| 1.6 | Devanagari PDF font bundle in WeasyPrint | Today Hindi career names render as boxes in PDF | Sample report PDF readable in Acrobat + Preview |
| 1.7 | Real Lighthouse perf budgets | Currently warn-only | Performance ≥ 0.85 enforced (error) |
| 1.8 | Razorpay full company KYC (Pvt Ltd) | Friend-KYC v1 caps at ₹5L cumulative GMV | Company GSTIN + Pvt Ltd cert filed |

## Q4 2026 — Growth ("v1.5")

**North-star metric:** 10,000 organic completions / 7-day rolling, ≥ 0.7%
free → paid conversion.

| ID | Item | Why | Acceptance |
| --- | --- | --- | --- |
| 2.1 | Hindi UI completion (Devanagari, not Hinglish) | Tier-2/3 reach | All STRINGS keys have native Devanagari hi values |
| 2.2 | Tamil + Bengali + Telugu + Marathi UI | South India + East India unlock | New language toggle row, content for label/slogan only |
| 2.3 | Result page A/B framework | Optimise for share rate + conversion | 50/50 split, 14-day power calc tool |
| 2.4 | Auth modal at `/test` Q40 (instead of unlock) | Capture intent earlier | A/B test: payable rate ≥ control |
| 2.5 | Dashboard `/dashboard` historical view + revisit | Repeat visits + "I changed" insights | Logged-in users see all past assessments |
| 2.6 | DELETE `/api/v3/assessment/{id}` | DPDPA compliance + privacy promise | One-click in `/dashboard` |
| 2.7 | Webhook idempotency keys | Razorpay retries can double-process | DB unique on `(event_id)` |
| 2.8 | OG image rotation (3+ variants per archetype) | Share-CTR | A/B winner per cell ships |
| 2.9 | Career library × ARCHETYPE refresh (200+ careers) | Shallow tail today | Each archetype has 8-10 careers, not 5 |
| 2.10 | Refer-a-friend: every share earns 50% off | Low-cost referral loop | LandingClient renders referral pill if `?ref=` |
| 2.11 | **Stretch:** counsellor B2B portal | Schools + colleges buy bulk codes | "Code redemption" flow, admin dashboard for code-issue org |

## Q1 2027 — "Smart MindPrism"

**North-star metric:** 100 paid users/day; introduce a higher-ticket
SKU (Career Plan ₹499) targeting 5–10% upsell.

| ID | Item | Why | Acceptance |
| --- | --- | --- | --- |
| 3.1 | LLM-personalised report (GPT-5 / on-device Llama) | Dynamic prose, not template | Ships behind feature flag, fallback to template |
| 3.2 | "Career Plan ₹499" SKU | 6-month cadence, weekly nudges | Stripe + Razorpay subscription, dashboard upsell |
| 3.3 | Resume / interview-question generator | Action-oriented use of archetype | LLM prompt with archetype + role; cached per `(cell, role)` |
| 3.4 | Career-path simulator | "Where will you be in 5 yrs if you choose X?" | Template-driven first, LLM-enhanced later |
| 3.5 | Real Indian company partnerships | Direct hiring CTAs | Internal API for `(cell → company match)` referrals |
| 3.6 | Mentor matching | Top-matched archetypes book 30-min calls | Out-of-product (Calendly + Stripe payment), in-product CTA |
| 3.7 | RIASEC 60-item full version (premium) | More-rigorous re-test | Behind ₹499 SKU |
| 3.8 | Mobile app (React Native + Expo) | Re-engagement push, dashboard | TestFlight / Play closed beta |
| 3.9 | **Stretch:** Couples / family edition | "Compare archetypes" — 2 → joint report | Free for 2; share + roast; viral hook |

## Q2 2027 — Platform

| ID | Item | Why | Acceptance |
| --- | --- | --- | --- |
| 4.1 | Public read API + dev portal | Third-party developers (HR SaaS, school CRM) | OpenAPI key auth, ratelimits, billing |
| 4.2 | Spec compliance: SOC 2 Type 1 + DPDPA audit | B2B sales unlock | Audit report shareable under NDA |
| 4.3 | Multi-region read replica | Latency for ASEAN expansion | <200ms p95 in SG, KL, JKT |
| 4.4 | English-as-second-language non-Indian markets | Bangladesh, Sri Lanka, Pakistan | New `region` cell variants |
| 4.5 | Org-led admin: HR, school counsellors | Bulk reports, manager dashboards | Multi-tenant w/ per-org branding |
| 4.6 | **Stretch:** Open-source the question library | Brand-building + research goodwill | Apache 2.0 fork-able items |

## Long-term bets (2028+)

- IRT (Item Response Theory) calibration of all items, dynamic
  difficulty adjustment.
- Adaptive testing — fewer questions for high-confidence archetypes.
- "Career genome" longitudinal: re-test every 6 months, plot drift.
- Voice-first taking the test (Hindi voice → Likert).
- Workplace integration: Slack bot, Notion dashboards, "team
  archetype mix" reports.

## What we're explicitly NOT doing

| Avoided | Why |
| --- | --- |
| Astrology / numerology / Vastu | Brand: scientific. Slippery slope. |
| MBTI letters (E/I, S/N, T/F, J/P) | Reliability < 0.7 in independent reviews; we use Holland + Big Five |
| Performance / IQ tests | Out of scope; different product |
| Recommend universities / colleges | Conflict of interest unless paid; we recommend roles, not specific institutions |
| Push notifications until v2 mobile | Email + WhatsApp link is enough |
| Crypto / Web3 | Not relevant to target market |

## Tracking & re-planning

- Each quarter: 1-page memo retro + reset of north-star metric.
- Items move quarters with a date stamp; nothing rots silently.
- Decisions that change PRODUCT.md or ARCHITECTURE.md must include a
  doc-update PR.
