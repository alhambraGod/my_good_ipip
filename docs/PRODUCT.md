# MindPrism — Product Document

> Product, positioning, and full user-journey description. Source of truth
> for what MindPrism *is* (separate from `ARCHITECTURE.md` for what it
> looks like in code, and `ROADMAP.md` for what's next).
>
> _Brand history: launched as **MindIQ** (Big-Five-only assessment, 2025),
> renamed **CareerDNA** during the IPIP-NEO + Holland RIASEC redesign
> (Apr 2026), and consolidated under the umbrella brand **MindPrism**
> (May 2026)._

---

## 1. One-line pitch

A 5-minute, science-backed personality + career test built for Indian
Gen-Z. 45 questions → one of 24 archetypes → matched career paths in
INR — free archetype, paid deep dive (₹49 early-bird, ₹99 standard).

## 2. Why this product

- **Indian audience under-served.** Western career tests
  (16Personalities, MBTI variants) use US salaries and culturally
  irrelevant prompts ("would you join a fraternity?"). Indian users
  resonate poorly.
- **Two unsolved tensions:**
  1. *Buzzfeed quizzes* are viral but vibe-driven; *real psychometric
     tools* (RIASEC, Big Five) are scientific but boring and English-only.
  2. Indian families equate career = IIT/IIM/MBBS; "what suits you" is
     an under-represented decision dimension.
- **Pricing reality.** ₹49 (~$0.60) is the sweet spot — high-school
  pocket-money territory; instant unlock; converts where Western
  $9.99 tests don't.

## 3. Who it's for

| Segment | Trigger | Hook |
| --- | --- | --- |
| Class 11–12 students | "Should I take Science or Commerce?" | Holland fit + parental-pressure framing |
| Engineering undergrads | Coding-job vs. UPSC vs. MBA dilemma | Archetype + Indian-company match list |
| Early-career (22–30) | Switching from TCS/WITCH to startups | OCEAN + city-tier-aware salary band |
| Returning workers / switchers | Career-second-act anxiety | Strengths/growth + share-back-to-friends |

Geographically: Tier-1 / Tier-2 India + diaspora; primary surfaces are
**WhatsApp, Instagram stories, X/Twitter India**. v1 ships English with
Hindi (Romanized + some Devanagari) toggle.

## 4. Theoretical foundation

| Model | What it gives | How we use it |
| --- | --- | --- |
| **Holland RIASEC** (J. L. Holland, 1959–1997, 30k+ citations) | 6 vocational interests on a hexagon: Realistic / Investigative / Artistic / Social / Enterprising / Conventional | Top 2 types → 6×4 = **24 archetype cells** (e.g., `IA` = Investigative-Artistic) with India-flavored labels |
| **Big Five (IPIP-NEO)** | 5 personality dimensions: Openness / Conscientiousness / Extraversion / Agreeableness / Neuroticism | OCEAN scoring on 0–100 + percentiles, used for fine-grained personalisation in the paid report |
| **MAST** (Multivariate Archetype Significance Trigger) | Statistical "rare profile" detector | If a respondent is multi-σ extreme (top-tier OCEAN + RIASEC tail), we flag them as a rare archetype subtype to reward virality |
| **IBTI tonality** (internal viral framework) | "Roast-style" Hinglish humour for slogans | Injected into archetype label + slogan, never into scientific items |

## 5. The 24 archetypes

24 cells = 6 RIASEC primary × 4 secondary (the four nearest hexagon
neighbours). Each cell ships with India-tuned content:

- `cell_id` (2 letters), `label_en`, `label_hi`
- `slogan_en` (1-line), `core_insight_en` (4–6 sentences),
  `deep_description_en` (1500+ chars), `strengths_en[5]`, `growth_tips_en[5]`
- `career_directions[]` (5+ matched careers from the central library)
- `rarity_pct` (population frequency band)

Examples (full set in `backend/content/data/cells/*.json`):

| Cell | Label | Slogan |
| --- | --- | --- |
| **IA** | The 3AM Chai Philosopher | "You overthink your overthinking. Also this sentence." |
| **EC** | The Spreadsheet Founder | "Vision plus VLOOKUP." |
| **SE** | The Glue | "You bring people together." |
| **AS** | The Reluctant Performer | "Talent that hides under hostel-room covers." |
| **RC** | The Quiet Builder | "Fix the thing nobody else can be bothered to fix." |
| **CI** | The Pattern Hunter | "Spreadsheets are your Bollywood." |

## 6. The career library

A curated set of ~78 careers (in `backend/content/data/careers/library.json`),
each with:

- `name_en` + `name_hi` (Devanagari for ~90% of entries)
- `tagline_en` (1-line role description)
- `why_match` — keyed by archetype `cell_id`, the role-fit explanation
  varies per archetype
- `salary_inr` — `entry / mid / senior` ranges in lakh / crore notation
- `indian_companies` — real hiring companies (Razorpay, Swiggy, TCS,
  Marwari business families, etc.)
- `education_path` — typical streams / certifications
- `city_distribution` — Bangalore / Hyderabad / Mumbai / NCR / Pune /
  Tier-2 capitals / remote

The career library is one-way referenced: archetype cells point to
careers, but careers can be referenced by **multiple** cells with
different `why_match` strings. A `find_dormant_why_match_entries()`
validator tracks careers whose `why_match` no longer matches a cell
that links to them.

## 7. The user journey

```
landing /                                        ← saffron-green hero, 24-archetype gallery,
                                                   FAQ, India-flavoured copy, EN/Hindi toggle
        │
        ▼
quiz /test                                       ← 5 demographic + 40 dynamic Likert
                                                   - keyboard 1-5 shortcuts
                                                   - localStorage progress autosave
                                                   - back-one / restart buttons
                                                   - milestone screens at Q10 / 20 / 30 / 40
                                                     with deterministic Hinglish copy
        │
        ▼
free results /results/[id]                       ← 5-screen scroll:
                                                   1. archetype card + rarity %
                                                   2. Holland radar
                                                   3. core insight
                                                   4. top 1 career unlocked + 4 locked teasers
                                                   5. dual CTA (share + unlock)
        │
        ▼
soft paywall /payment                            ← real-time price (₹49 promo / ₹99 full),
                                                   promo-quota progress bar,
                                                   Razorpay Checkout SDK (in-page modal)
        │
        ├── /payment/success                     ← verifies Razorpay signature, writes paid=True
        │
        ▼
deep report /report/[id]                         ← sticky TOC + scroll-spy, Hindi-aware
                                                   - cell deep dive (1500+ char prose)
                                                   - strengths × growth tips
                                                   - OCEAN + percentiles
                                                   - 5+ career matches with INR salary,
                                                     why-match, hiring companies, cities
                                                   - PDF download (WeasyPrint)
        │
        ▼
sharing                                          ← `/s/{code}` short links (302 redirect),
                                                   `/api/og/[id]` Edge ImageResponse cards,
                                                   pre-rendered WhatsApp / X copy
```

## 8. Free vs. paid

| | Free results page | Paid deep report |
| --- | --- | --- |
| Archetype cell + label | ✓ | ✓ |
| Slogan + rarity % | ✓ | ✓ |
| Holland radar | ✓ | ✓ |
| Core insight (4 sentences) | ✓ | ✓ |
| **Top 1 career match** | ✓ (with salary band) | ✓ |
| **Other 4+ careers** | locked teaser | ✓ unlocked |
| Deep description (1500+ chars) | — | ✓ |
| Strengths × Growth tips | — | ✓ (5 each) |
| OCEAN profile + percentiles | — | ✓ |
| Education + city + company match per career | — | ✓ |
| PDF | — | ✓ |
| Share lines + OG cards | ✓ | ✓ |

Soft paywall by design: ~6% of total useful content is gated; the free
view is genuinely shareable.

## 9. Pricing

| Variant | INR | $ approx | Status |
| --- | --- | --- | --- |
| **Promo (early-bird)** | ₹49 | $0.60 | First 1,000 reports, then auto-rolls to standard |
| **Standard** | ₹99 | $1.20 | After promo quota |

Quota state is queryable: `GET /api/v3/payment/price` returns
`{ amount_inr, promo_active, promo_remaining, promo_cap }` and the
payment page renders a live progress bar.

Future: regional discounts, gift codes, bulk B2B (school career counsellors).

## 10. Localization & cultural fit

- **Languages.** English (primary) + Hindi (Hinglish + Devanagari for
  career names). User toggles via `<LangToggle />`; persisted in
  `localStorage`. v2 will add Tamil / Bengali / Telugu / Marathi.
- **Cultural markers integrated.**
  - Honorifics: "Sharma ji's beta", "Aunty"
  - Family / society: joint-family pressure, EMI math, log kya
    kahenge, IIT / IIM scripts, "settle" pressure
  - Cities: Tier-1 (Bangalore, Mumbai, Delhi-NCR, Hyderabad, Chennai,
    Pune, Kolkata) and Tier-2 capital tracking in career
    distributions
  - Companies: Razorpay, Swiggy, Zomato, Flipkart, Paytm, Tata,
    Infosys, TCS, Wipro (the "WITCH"), Reliance, Marwari trader
    networks, government PSU
- **Sensitive topics avoided.** No religion, no caste, no political
  party allegiance, no specific community stereotyping.

## 11. Sharing surface

| Surface | Hook |
| --- | --- |
| **Free results page** | Pre-written WhatsApp share line, "Share to WhatsApp" CTA |
| **Result OG image** | `/api/og/[id]` returns dynamic 1200×630 PNG with archetype id, label, slogan, brand stripe |
| **Short link** | `/s/{code}` 302-redirects to `/results/[id]`; click counter on `ShortLink` row |
| **Archetype detail page** | Long-tail SEO; one URL per cell (24 total), each on the sitemap |
| **Sitemap** | `/sitemap.xml` lists `/`, `/archetypes`, all `/archetypes/[cell]`, all updated weekly/monthly |

## 12. Privacy + data ethics

- No third-party ad pixels.
- No data resale.
- Free path stores only: anonymous answers, scores, archetype, optional
  short-link code. No login required.
- Paid path: assessment can optionally be linked to a `UserProfile`
  (Google / Facebook / WhatsApp / Email) so the user can email
  themselves the report.
- `/dashboard` lists the user's own past assessments; admin endpoints
  do not expose other users' answers.
- "Email support to delete your data" is currently the manual pathway;
  v2 ships `DELETE /api/v3/assessment/{id}`.

## 13. Compliance & risk

- **Not a clinical assessment.** Disclaimer is on every footer, the
  payment page, and the report.
- **Razorpay KYC.** v1 uses an Indian friend's personal KYC for the
  Razorpay merchant; full company KYC will move to a registered Pvt
  Ltd before crossing ₹5L cumulative GMV.
- **GDPR / DPDPA.** Data minimisation already enforced (no PII at
  free stage). DPDPA Section 8 (rights to correction & erasure)
  documented in privacy copy; ticketing pathway is the same as data
  delete.
