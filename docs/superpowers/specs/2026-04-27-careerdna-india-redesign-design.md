# CareerDNA India Redesign — Design Spec

**Status**: Draft v1.0 · 待 user review
**Date**: 2026-04-27
**Owner**: Antonio
**Spec format**: Brainstorming → Spec → Implementation Plan (writing-plans skill)

---

## 0. TL;DR

把现有 100 题纯 Big Five MindIQ 测评升级为 **45 题混合 IPIP-NEO + Holland RIASEC 测评**，结果页注入 IBTI 印度本土病毒 DNA，UI 全面切到印度橙绿混血风。单产品 CareerDNA，结果页同时承担"病毒分享"和"付费转化"双职责。

会议纪要的 15 项需求逐条落地，不做独立 IBTI 病毒前端漏斗（v2 再考虑）。

---

## 1. Goals

### 1.1 Business Goals

1. **印度市场冷启动**：通过 WhatsApp 病毒分享拿到首批 1,000-10,000 用户
2. **付费转化**：免费做完 45 题 → 看摘要 → 解锁完整报告，目标转化率 0.5-1%（参考 IBTI 文档预估的 0.6-0.7%）
3. **科学背书**：保留 IPIP-NEO + Holland RIASEC 严肃测评底层，避免被认为是"娱乐性 buzzfeed quiz"

### 1.2 Non-Goals (v2 再做)

1. 独立 IBTI 31 题病毒漏斗（产品 B 路线）
2. 完整 Hindi/Tamil/Bengali/Marathi 翻译
3. DARU 酒精彩蛋（合规风险高）
4. 多币种、Devanagari PDF 字体
5. Razorpay 商户级账户（v1 用印度朋友个人 KYC）
6. IRT 等价校准 / RIASEC 题目动态化（L2 全动态）

---

## 2. Architecture Overview

### 2.1 System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Frontend (Next.js 16)                       │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────────┐   │
│  │  Landing   │→ │  /test     │→ │ /analyzing │→ │  /results    │   │
│  │  (印度调性) │  │ 45 题动态   │  │  动画      │  │ 5 屏滚动     │   │
│  └────────────┘  └────────────┘  └────────────┘  └──────────────┘   │
│                       ↓ Q10/20/30/40 milestone                       │
│                  ┌─────────────────┐                                 │
│                  │ /share/[id].png │ (OG image)                      │
│                  └─────────────────┘                                 │
│                                                                       │
│                  Auth modal triggered ONLY at "Unlock"                │
└─────────────────────────────────────────────────────────────────────┘
                              ↓ JSON / cookie session
┌─────────────────────────────────────────────────────────────────────┐
│                       Backend (FastAPI)                              │
│  ┌──────────────┐ ┌──────────────┐ ┌─────────────┐ ┌──────────────┐ │
│  │ assessment/  │ │ scoring/     │ │ payment/    │ │ report/      │ │
│  │ - select 45  │ │ - RIASEC     │ │ - razorpay  │ │ - 24-cell    │ │
│  │ - submit     │ │ - OCEAN      │ │ - wechat    │ │ - PDF        │ │
│  │ - milestones │ │ - cell match │ │ - mock      │ │ - share OG   │ │
│  └──────────────┘ └──────────────┘ └─────────────┘ └──────────────┘ │
│         ↓                ↓                 ↓               ↓         │
│    SQLite/Postgres  Question Banks   Payment Drivers   Content Lib   │
│                     (RIASEC 60       (Strategy         (24 cells +   │
│                      + IPIP 120)      pattern)          40 careers)  │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Core Decisions (locked in brainstorming)

| Decision | Choice | Rationale |
|---|---|---|
| **Product form** | C: Single product CareerDNA + IBTI viral DNA in result page | Lowest engineering cost while keeping virality |
| **6-type framework** | Holland double-letter codes (hexagon adjacency) — 6 main × 4 sub = 24 cells | Mathematical 24 alignment + scientific theory + Indian-flavored labels |
| **OCEAN role** | Not in cell classification, only fine-grained personalization in report text | Clean separation, OCEAN data not wasted but doesn't muddle the cell logic |
| **Question structure** | 5 demographic + 24 RIASEC + 16 IPIP-NEO/interest = 45 | Reliable α coefficients; clean phase separation |
| **Dynamic logic** | L1.5: RIASEC 24 static (cross-user comparable); IPIP/interest 16 dynamic by demographic | Science + personalization + manageable complexity |
| **Result page** | 5-screen scroll + soft paywall ~6% + 3 share touchpoints | Maximizes virality and conversion |
| **Login binding** | Only at "Unlock" click (Screen 5) | Removes friction during quiz + result browsing |
| **Payment** | Razorpay personal account (印度朋友 KYC) | Auto-confirmation UX, evades company registration delay |
| **OAuth providers** | Email magic link + WhatsApp + Google + Facebook | Aligned with meeting requirements; Twitter/Telegram hidden in v1 |
| **Visual style** | C: Indian saffron+green hybrid IBTI tonality | Scientific + viral + locally rooted |
| **Localization** | English with Hinglish accents, 40 career library, INR/lakh, MAST kept, DARU dropped | v1 sweet spot: high local feel, low compliance risk |

---

## 3. Subsystem Designs

### S1 · Question Bank Infrastructure

#### 3.1 Sources

- `docs/IPIP_NEO_120_questionbank.json` — 120 IPIP-NEO items (5 OCEAN domains × 6 facets × 4 items)
- `docs/Holland_RIASEC_60_questionbank.json` — 60 Holland items (6 RIASEC types × 10 items)

#### 3.2 New Storage Layout

Move from monolithic `backend/questions/question_bank.py` to a modular structure:

```
backend/questions/
  __init__.py
  ipip_neo.py            # IPIP-NEO 120 loader + helpers
  holland_riasec.py      # Holland RIASEC 60 loader + helpers
  demographic.py         # 5 demographic questions (defined in code)
  interest_pool.py       # 30+ Indian-flavored interest items (curated, IBTI-style)
  selector.py            # L1.5 dynamic selection engine
  models.py              # Question, QuestionMetadata, QuestionSet dataclasses
```

#### 3.3 Question Object Schema

```python
@dataclass
class Question:
    id: str                      # e.g., "RIASEC_R_01", "IPIP_N81", "DEM_AGE", "INT_EMI_01"
    text_en: str                 # English text (v1 primary)
    text_hi: str | None          # Hindi text (v2 placeholder, None in v1)
    instrument: Literal["riasec", "ipip", "demographic", "interest"]
    dimension: str               # "R"/"I"/"A"/"S"/"E"/"C" or "openness"/"conscientiousness"/...
    facet: str | None            # IPIP facet like "N1_anxiety"; None for RIASEC
    reverse: bool                # Reverse scoring flag
    response_type: Literal["likert_5", "single_choice", "multi_choice"]
    options: list[dict] | None   # For demographic/interest with custom choices
    scenes: list[str]            # ["student", "fresher", "experienced", "switcher", ...]
    role: Literal["core", "scene", "reverse", "filler"]
    difficulty: Literal["easy", "medium", "hard"]
    tags: list[str]              # ["india", "career", "humor", "family-pressure", ...]
    weight: float = 1.0          # Selector preference weight
```

### S2 · Dynamic Question Selection (L1.5)

#### 3.4 Selection Algorithm

```python
def select_45_questions(demographic_answers: dict) -> list[Question]:
    # Phase 1: 5 demographic (always identical, in fixed order)
    questions = list(get_demographic_set())  # 5 items

    # Phase 2: 24 RIASEC (FULLY STATIC — same for all users)
    # Hand-picked from 60-item Holland bank: 4 best per type
    riasec_24 = get_riasec_static_24()  # constant

    # Phase 3: 16 IPIP-NEO + interest (DYNAMIC by demographic)
    profile_tags = derive_profile_tags(demographic_answers)
    # e.g., student → ["student", "campus", "future-explore"]
    #       experienced → ["work-stress", "family-pressure", "EMI"]

    candidate_pool = get_ipip_interest_pool()  # 30-40 items
    selected_16 = weighted_sample(
        pool=candidate_pool,
        tags=profile_tags,
        constraints={
            "ocean_coverage": {dim: 3 for dim in ["O","C","E","A","N"]},  # ≥3 per dim
            "interest_max": 1,  # at most 1 unique interest item per OCEAN dim
        },
        n=16,
    )

    # Phase 4: Interleave RIASEC + IPIP/interest, NOT 24 then 16
    interleaved = interleave_pattern(riasec_24, selected_16)
    # Pattern: e.g., 1 RIASEC, 1 RIASEC, 1 IPIP, 1 RIASEC, 1 IPIP, ... (varies by total)

    return questions + interleaved  # 45 total
```

#### 3.5 Demographic Questions (Fixed v1 set)

```python
DEMOGRAPHIC_5 = [
    {"id": "DEM_STAGE", "prompt": "Which best describes you right now?",
     "options": ["Student", "Fresher (≤2 yr work)", "Working Professional", "Career Switcher", "Founder/Self-employed"]},
    {"id": "DEM_AGE", "prompt": "Your age band",
     "options": ["15-19", "20-24", "25-29", "30-34", "35+"]},
    {"id": "DEM_GENDER", "prompt": "Gender",
     "options": ["Male", "Female", "Non-binary", "Prefer not to say"]},
    {"id": "DEM_CITY_TIER", "prompt": "Where do you live?",
     "options": ["Tier-1 (Mumbai/Delhi/Bangalore/Chennai/Hyderabad/Pune)", "Tier-2", "Tier-3 / Town", "Outside India"]},
    {"id": "DEM_TOP_PRESSURE", "prompt": "What's pressing you most these days?",
     "options": ["Career direction", "Family expectations", "Money/EMI", "Self-doubt", "Just curious"]},
]
```

#### 3.6 Milestone Encouragement Pages

After Q10 / Q20 / Q30 / Q40 the frontend displays a brief milestone screen:

- Progress ring (current % done)
- One-liner from a pool of 4–6 randomized Hinglish-flavored copy:
  - `10 done. Your patience already beats 60% of users.`
  - `Halfway. Even Sharma ji's beta started here.`
  - `Almost there. Your career insight is loading.`
  - `5 more. Don't bail. Aunty's watching.`
- "Continue" button (non-blocking)

### S3 · Scoring Model

#### 3.7 Score Computation

```
RIASEC scores (per type, range 4–20):
  raw_R = sum(answers[q.id] for q in riasec_questions if q.dim == "R")
  # 4 questions × 5-point scale = 4–20 range

OCEAN scores (per domain, range 3–15 because 3 items per dim, or 0–100 normalized):
  raw_O = sum(reverse_if_needed(answers[q.id]) for q in ipip_questions if q.dim == "openness")
  # Normalize to 0–100 percentile against IPIP norms
  ocean_O_pct = percentile_lookup(raw_O, "openness")

Holland code (top 3 RIASEC):
  holland_code = "".join(top_3(riasec_scores))  # e.g., "IRC", "SAE"

Archetype cell (24 cells):
  main_type = holland_code[0]   # e.g., "I"
  sub_type  = holland_code[1]   # e.g., "R" (must be valid neighbor)
  if (main_type, sub_type) is opposite-pair (e.g., I+E forbidden):
      sub_type = holland_code[2]  # use third letter instead
  archetype_cell = main_type + sub_type   # e.g., "IR", "IA", "IC", "IS"
```

#### 3.8 Hexagon Adjacency Rules

```
RIASEC hexagon order: R - I - A - S - E - C - R (cycle)
Forbidden opposite pairs (distance 3):
  R ↔ S, I ↔ E, A ↔ C

Each main type's 4 valid sub-types:
  R → I, A, E, C (excluding S)
  I → R, A, S, C
  A → I, R, S, E
  S → I, A, E, C
  E → R, A, S, C
  C → I, R, S, E

Total = 6 × 4 = 24 archetype cells
```

#### 3.9 OCEAN's Role in Reports

OCEAN does **NOT** affect cell classification. It enters the report at **content generation time**:

```python
def generate_report(cell: str, ocean_pct: dict, demographic: dict) -> ReportData:
    base = CELL_TEMPLATES[cell]    # base description, 24 templates
    ocean_modifiers = derive_modifiers(ocean_pct)
    # e.g., "high conscientiousness" → adds "你倾向严谨实战派而非理论派"
    #       "low emotional stability" → adds "压力下你需要主动设节律"
    return ai_compose(base, ocean_modifiers, demographic)  # GPT-4o
```

### S4 · 24-Cell Content Library

#### 3.10 Cell Naming (preliminary, can be tuned)

| Cell | English Label | Hinglish Tag | IBTI 灵感 | 主推职业方向（印度市场）|
|------|---------------|--------------|-----------|---------------------|
| RI | The Bangalore Engineer | Practical Coder | CODR | Software dev · DevOps · Embedded |
| RA | The Maker-Artisan | Hands-on Designer | — | Industrial design · Architecture · Crafts |
| RE | The Site Foreman | The Hustler Lead | SETH-lite | Project management · Manufacturing · Logistics |
| RC | The Disciplined Technician | EMI-Ready Engineer | EMII-lite | Electrical/Electronics · QA · Mechanical |
| IR | The Lab Realist | Disciplined Researcher | CODR-rev | Data engineering · Applied research · ML eng |
| IA | The 3AM Chai Philosopher | Sochne Wala | OVER | Strategy consulting · Data science · Academic |
| IS | The Empathic Investigator | Counselor Scholar | — | Clinical psych · EdTech research · Public health |
| IC | The Quiet Analyst | Number Cruncher | — | Data analytics · Risk · Quant finance |
| AI | The Indie Auteur | The Lone Creator | AKEL+CHUT | Indie filmmaker · Concept artist · Content creator |
| AR | The Craft Maverick | Hands-On Artist | — | Film production · Photography · Industrial design |
| AS | The Bollywood Storyteller | DDLJ Spirit | DDLJ | Screenwriter · Director · Therapist (creative) |
| AE | The Brand Auteur | Entertainment Hustler | ITEM | Brand creative · Fashion · KOL/Creator |
| SI | The Reflective Mentor | Thoughtful Teacher | — | Counseling · Academic mentor · NGO advisor |
| SA | The Healing Performer | Drama Therapist | PAGL | Art therapy · Edu performer · Child psych |
| SE | The Marwari Mentor | Sales Coach | LINK | Sales mgmt · HR consulting · Edu admin |
| SC | The All-Knowing Aunty | Aunty-Mode | AUNT | HR · Customer success · Govt advisory |
| ER | The Hustle Founder | Startup Operator | JUGA | Founder · BD · Product manager |
| EA | The Showrunner | Bollywood Producer | — | Media management · Creative director · Brand |
| ES | The Charismatic Closer | LinkedIn Influencer | LINK | Sales · Business dev · PR |
| EC | The Marwari Mindset | Empire Builder | SETH | Investment · Cross-border e-comm · Wealth mgmt |
| CI | The Compliance Brain | Sarkari Analyst | — | Audit · Legal compliance · Financial analysis |
| CR | The Operations Backbone | Disciplined Doer | — | Operations · Production · Inventory mgmt |
| CS | The Customer Steward | BPO Soul | SRRY | Customer service · Admin · Training mgmt |
| CE | The Sarkari Babu | Quiet Puppetmaster | BABU | Govt/Public · Project mgmt · Operations mgmt |

#### 3.11 Content Per Cell

Each cell has a JSON content file:

```
backend/content/cells/{cell}.json
{
  "cell": "IA",
  "label_en": "The 3AM Chai Philosopher",
  "label_hi": "Sochne Wala",
  "slogan_en": "You overthink your overthinking. Also this sentence.",
  "rarity_pct": 4.3,
  "core_insight_en": "你脑子里 87 个 Chrome tab 都打开着。86 个是关于过去的。你想得多，做得少...",
  "deep_description_en": "...300-500 字 paid-only deep dive...",
  "strengths": ["Pattern recognition", "Strategic foresight", "Independent learning", "Synthesis across fields", "Comfort with ambiguity"],
  "growth_tips": ["Set timeboxes for analysis", "Ship 70%-ready outputs", "Use peer rubber-ducking", "Externalize anxiety to journals", "Adopt a do-1-thing daily ritual"],
  "career_directions": ["data_scientist", "strategy_consultant", "quant_analyst", "academic_researcher", "ai_research_eng", "policy_analyst"],
  "share_lines": [
    "I'm IA. My personality is just Stack Overflow with trust issues.",
    "I'm IA. I overthink my overthinking. Also this sentence.",
    "I'm IA. 4.3% rare. I'd celebrate but I'm too busy doubting myself."
  ],
  "ocean_modifiers": {
    "high_conscientiousness": "Your high conscientiousness pulls IA toward rigorous execution rather than pure theory.",
    "low_emotional_stability": "Under stress, you need to externalize the loop — write it down or talk it out.",
    "high_openness": "Your novelty-seeking can pull you across fields; consider a meta-discipline as your home base."
  }
}
```

24 such files. v1 written by author + GPT-4o pass + manual review.

### S5 · Career Library

#### 3.12 Schema (40 careers, India-tuned)

```
backend/content/careers/library.json
{
  "data_scientist": {
    "name_en": "Data Scientist",
    "name_hi": "Aankde Vigyani / डेटा साइंटिस्ट",
    "tagline": "Turn chaos into signal",
    "why_match": {
      "IA": "你天生擅长从混乱数据里看到 pattern, India IT/fintech demand is booming",
      "IC": "你的 numerical brain + structured thinking 直接对应这岗位",
      "IR": "Your engineering rigor makes you go from analyst to ML engineer fast"
    },
    "indian_companies": ["Razorpay", "Swiggy", "Flipkart", "Mu Sigma", "Fractal Analytics", "TCS Research"],
    "salary_inr": {"entry": "6L", "mid": "12L–22L", "senior": "30L–80L"},
    "education_path": ["B.Tech CSE/Stats", "Master's preferred for research roles", "Online: Coursera/DataCamp"],
    "city_distribution": ["Bangalore", "Hyderabad", "Pune", "Gurugram"]
  },
  "strategy_consultant": { ... },
  "screenwriter": { ... },
  ...40 careers
}
```

40 careers spanning: IT (12) · Finance (6) · Media/Arts (6) · Education/Research (4) · Sales/Ops (5) · Entrepreneurship (3) · Government (2) · Service (2).

### S6 · Result Pages & Paywall

#### 3.13 Five-Screen IA

```
/results/[id]  →  full free experience, no login wall
   ┌───────────────────────────────────────────────┐
   │ Screen 1 · Personality Card                    │
   │   - Big code "IA" + label "The 3AM Chai..."    │
   │   - Slogan + rarity %                          │
   │   - Saffron-green gradient + diya 🪔           │
   │   - "Share to WhatsApp" → opens deep link      │
   ├───────────────────────────────────────────────┤
   │ Screen 2 · Holland Radar                       │
   │   - 6-axis radar chart, main+sub highlighted   │
   │   - "Investigative-dominant + Artistic-supp."  │
   │   - "Save image" → @vercel/og PNG              │
   ├───────────────────────────────────────────────┤
   │ Screen 3 · Core Insight (free, 80–120 words)   │
   │   - Bilingual flavor (Hinglish accent words)   │
   │   - Matches the cell's core_insight_en field   │
   ├───────────────────────────────────────────────┤
   │ Screen 4 · Career Teaser (5% paywall)          │
   │   - Career #1: full name + 1-line why + ₹range │
   │   - Career #2: name visible, body blurred      │
   │   - Careers #3–6: full names blurred           │
   │   - "Unlock 4 more career paths →"             │
   ├───────────────────────────────────────────────┤
   │ Screen 5 · Dual CTA (核心转化处)                │
   │   ┌───────────────┬───────────────────────┐    │
   │   │ Share to friends │ Unlock full report  │    │
   │   │ • WhatsApp       │ • 5+ careers + ₹    │    │
   │   │ • Facebook       │ • OCEAN analysis    │    │
   │   │ • Copy link      │ • Strengths × 5     │    │
   │   │                  │ • Growth tips × 5   │    │
   │   │                  │ • PDF (English v1)  │    │
   │   │                  │ ₹99 (1st 1k: ₹49)   │    │
   │   │                  │ [Unlock →]          │    │
   │   └───────────────┴───────────────────────┘    │
   └───────────────────────────────────────────────┘

/report/[id]  →  appears AFTER payment success
   - Full deep description
   - Holland code 3-letter explanation
   - OCEAN 5-dim bars + 100-word interpretation each
   - Strengths × 5 (full)
   - Growth tips × 5 (full)
   - 5+ career paths with full body, companies, salary, paths
   - PDF download button (preview at /report/[id]/preview)
   - "Share your unlock" CTA (re-share post-payment)
```

#### 3.14 Paywall Math

| | Free Experience | Paid Report |
|---|---|---|
| Personality label | ✅ full | ✅ full |
| Slogan | ✅ full | ✅ full |
| Holland radar | ✅ full | ✅ full + 3-letter explained |
| Core insight | ✅ ~100 words | ✅ replaced by 300-500 word deep description |
| Strengths | ❌ | ✅ × 5 |
| Growth tips | ❌ | ✅ × 5 |
| OCEAN scores | ❌ | ✅ 5 bars + 5 × 100-word interpretations |
| Career #1 | ✅ name + 1-line why + salary range | ✅ + companies + path + city |
| Career #2 | name visible, body blurred | ✅ full |
| Careers #3–6 | name blurred | ✅ full |
| PDF | ❌ | ✅ |
| **Word count** | ~150 words visible | ~2,500 words total |
| **% visible** | **6%** | 100% |

This intentionally exceeds the meeting's "5%" guidance to keep the free page viscerally satisfying — viewers see the personality + 1 career and feel that "the science is real and locked behind a paywall," not "I got nothing."

### S7 · Auth & Payment

#### 3.15 Auth Flow

```
Anonymous user → starts test → cookie session (server-issued, stateless)
  → completes 45 questions, sees /results/[id]
  → clicks "Unlock" on Screen 5
  → modal: "Email magic link" / "WhatsApp" / "Google" / "Facebook"
  → after auth, link cookie session → user_id (creates UserProfile if needed)
  → redirect to payment intent
  → payment success → /report/[id] full report
```

OAuth providers v1: **Email magic link, WhatsApp, Google, Facebook** (Facebook is new — see migration).
v1 hidden: Twitter, Telegram (code retained).

#### 3.16 Payment Driver Architecture

```python
# backend/services/payment/
class PaymentDriver(Protocol):
    def create_payment_intent(assessment_id: str, amount_inr: int) -> PaymentIntent: ...
    def verify_webhook(payload: bytes, signature: str) -> WebhookEvent: ...

class MockDriver(PaymentDriver): ...      # always succeeds, dev mode
class WeChatDriver(PaymentDriver): ...    # 微信支付 — internal validation only
class RazorpayDriver(PaymentDriver): ...  # India production via personal merchant
class StripeDriver(PaymentDriver): ...    # legacy, kept for non-India users

# Routing by config
PAYMENT_MODE = "mock" | "wechat" | "razorpay" | "stripe"
```

v1 production default: `razorpay`. Razorpay supports Indian individual merchant accounts. Razorpay creates a **payment link** containing UPI Intent + Card + NetBanking; user redirected to Razorpay-hosted page; webhook signs back to backend for confirmation.

#### Pricing & Promo Rules

```python
# config.py
PRICE_FULL_INR = 99
PRICE_PROMO_INR = 49
PROMO_MAX_REDEMPTIONS = 1000  # first 1000 paid users get ₹49

def get_current_price() -> int:
    paid_count = db.query(Assessment).filter(Assessment.payment_status == "confirmed").count()
    return PRICE_PROMO_INR if paid_count < PROMO_MAX_REDEMPTIONS else PRICE_FULL_INR
```

UI shows both prices when promo is active (`₹49` with `~~₹99~~` strikethrough); shows only ₹99 after promo exhaustion. The price displayed at "Unlock" click time is the price charged (no race condition: backend re-validates count before creating Razorpay link).

### S8 · Sharing Infrastructure

#### 3.17 Share Surface

| Surface | Implementation |
|---|---|
| WhatsApp deep link | `https://wa.me/?text={encodeURIComponent(prefab_text + " " + short_url)}` |
| Facebook share | `https://www.facebook.com/sharer/sharer.php?u={short_url}&quote={prefab_text}` |
| Copy link | `navigator.share` API + clipboard fallback |
| OG image | `/api/share/[assessment_id]/og.png` via `@vercel/og` `ImageResponse` |
| Short link | Self-hosted: `/s/[code]` route → DB lookup → 302 to canonical URL |

#### 3.18 OG Image Layout

@vercel/og renders an 1200×630 PNG matching Screen 1 visual style:
- Saffron-green gradient bg
- Big "IA" code centered
- Tag "The 3AM Chai Philosopher"
- Slogan
- "Find yours at careerdna.in" footer
- Diya 🪔 + rarity badge

#### 3.19 Share Touchpoints (3 places on /results)

- Screen 1: "Share to WhatsApp" inline button
- Screen 2: "Save image" (downloads OG PNG)
- Screen 5: Full dual-CTA panel with all share methods

#### 3.20 Prefab Share Lines

3 patterns from IBTI doc, selected randomly per share click:

- **Self-roast**: `Bhai, this test called me out so hard I considered therapy. Got [IA]. Try it → [link]`
- **Surprise**: `Haw. This quiz just described my entire WhatsApp existence. I'm [IA]? Don't believe it till you try → [link]`
- **Challenge**: `Everyone in this group take this test and send your 4-letter code. Whoever gets [SC] (Aunty) first owes everyone chai → [link]`

### S9 · UI Visual Direction (Style C)

#### 3.21 Color Palette

```
Saffron / India orange:  #FF9933  (hero accent)
Deep saffron:            #B45309  (text on light)
Cream:                   #FFFAF0  (mid gradient)
India green light:       #C8E6C9  (mid gradient)
India green:             #138808  (CTA primary)
India green dark:        #15803D  (hover)
Navy text:               #1A202C  (body text)
Muted gray:              #6B7280  (secondary text)
```

#### 3.22 Typography

```
Display: Poppins (700/900 weight) — for personality codes, headlines
Body:    Inter or Sora — for paragraphs, options
Mono:    JetBrains Mono — for occasional code-style accents
```

#### 3.23 Page-Level Restyle (frontend pages)

| Page | New direction |
|---|---|
| `/` (Landing) | Hero with diya 🪔 + saffron-green gradient + "Find Your Indian Career DNA" + Hinglish accent |
| `/start` | Simplified onboarding (no demo questions here; demo is now Q1-5 of `/test`) |
| `/test` | One-question-per-screen, swipe-friendly, progress ring, milestone interrupts at Q10/20/30/40 |
| `/analyzing` | "We're decoding your IA..." with diya animation, ~3-5 sec |
| `/results/[id]` | NEW 5-screen scroll layout, no login wall, share buttons |
| `/payment` | Razorpay redirect (or mock confirm in dev) |
| `/report/[id]` | Full deep report with OCEAN + careers + share post-paid CTA |
| `/report/[id]/preview` | PDF preview (existing, restyled) |
| `/dashboard` | "Your IA history" — list of past assessments, retain-friendly |

### S10 · Localization

#### 3.24 v1 Scope (recap)

- **Language**: English primary, Hinglish accents in copy (`Sharma ji ka beta`, `Aapki personality`, `Tum overthink karte ho`). No language toggle.
- **Career library**: 40 careers, all bilingual labels (English + Devanagari transliteration), India-only company anchors, INR salary ranges in lakh notation.
- **Number format**: Indian (lakh / crore) where amounts apply.
- **Date format**: `DD/MM/YYYY` for any user-facing dates.
- **Religion / caste / politics / state-level**: hard red line, zero references.
- **DARU 彩蛋**: dropped in v1.
- **MAST 0.06% rare**: kept (no compliance risk, high virality).

#### 3.25 v2 Plan (out of scope here)

- Full Hindi translation (UI + reports + PDF, with Devanagari font in PDF)
- Tamil/Bengali/Marathi additions
- Multi-currency for NRI cohort
- DARU + IP/state-aware regional toggles

---

## 4. Data Model Changes

### 4.1 `Assessment` table (modify)

```python
class Assessment(Base):
    # Existing fields kept for backward compat
    id, created_at, completed, paid, profile_source, profile_data,
    profile_session_token, selection_seed
    # answers: JSON  → keep but format changes (id-keyed)

    # CHANGE: scoring fields restructured
    # scores: dict          ← REPLACE: now ocean_scores (dict of 5 dims, 0–100 percentile)
    ocean_scores = Column(JSON, nullable=True)         # {"O": 72, "C": 88, "E": 41, "A": 65, "N": 55}
    riasec_scores = Column(JSON, nullable=True)        # {"R": 12, "I": 19, "A": 17, "S": 9, "E": 11, "C": 13}
    holland_code = Column(String(3), nullable=True)    # e.g., "IRC"

    # NEW: archetype fields
    archetype_cell = Column(String(2), nullable=True, index=True)   # e.g., "IA"
    archetype_label_en = Column(String(80), nullable=True)
    archetype_rarity_pct = Column(Float, nullable=True)             # 4.3

    # NEW: demographic
    demographic = Column(JSON, nullable=True)          # {"DEM_STAGE":"Student", ...}

    # CHANGE: question_set_version → "v3_45_hybrid"
    question_set_version = Column(String, default="v3_45_hybrid")

    # NEW: share/short link
    share_code = Column(String(8), unique=True, nullable=True, index=True)

    # CHANGE: payment fields
    # stripe_session_id → payment_provider + payment_txn_id + payment_status
    payment_provider = Column(String, nullable=True)   # "razorpay"|"mock"|...
    payment_txn_id = Column(String, nullable=True)
    payment_status = Column(String, default="pending") # pending|confirmed|failed|refunded
    payment_amount_inr = Column(Integer, nullable=True)

    # NEW: report content (replaces report_markdown/html)
    report_data = Column(JSON, nullable=True)          # structured: {strengths, growth, careers, ocean_text, deep}
    pdf_path = Column(String, nullable=True)
```

Backward compat: keep old `scores`/`stripe_session_id`/`report_markdown` columns nullable for ≥1 release; new code reads `ocean_scores`/`payment_*`/`report_data`.

### 4.2 New table: `ShortLink`

```python
class ShortLink(Base):
    __tablename__ = "short_links"
    code = Column(String(8), primary_key=True)         # nanoid
    assessment_id = Column(String, ForeignKey("assessments.id"))
    target_url = Column(String, nullable=False)
    clicks = Column(Integer, default=0)
    created_at = Column(DateTime, default=now_utc)
```

### 4.3 No changes to `UserProfile` schema (keep as-is).

---

## 5. API Surface Changes

### 5.1 Existing endpoints (modify)

| Endpoint | Change |
|---|---|
| `GET /api/assessment/questions` | → returns 5 demographic + signal that next 40 will be selected after demo answers |
| `POST /api/assessment/start` | NEW: receives demographic, returns next 40 question IDs (RIASEC 24 + 16 dynamic) |
| `POST /api/assessment/submit` | Submit answers, triggers scoring + cell match + share_code generation |
| `GET /api/assessment/{id}/results` | Returns free 5-screen data (no OCEAN, no full careers) |
| `GET /api/report/{id}` | Returns full report (auth + paid required) |
| `GET /api/report/{id}/pdf` | PDF download (paid-only) |
| `POST /api/payment/create-intent` | Returns Razorpay payment link |
| `POST /api/payment/webhook/razorpay` | NEW: webhook for Razorpay confirmation |
| `POST /api/auth/facebook/...` | NEW: Facebook OAuth |
| `GET /s/[code]` | NEW: short link → 302 to canonical results URL |
| `GET /api/share/[id]/og.png` | NEW: dynamic OG image |

### 5.2 Removed (v1)

- `POST /api/payment/stripe/...` deprecated for Indian users (keeps for non-India)

---

## 6. Migration Plan (high level — detailed in implementation plan)

**Phase 0 · Prep (1 week)**
- Backup current DB; tag git baseline
- Add new columns nullable; deploy schema migration
- Razorpay personal account KYC (offline,印度朋友配合)
- Facebook OAuth app registration

**Phase 1 · Question Bank + Scoring (1.5 weeks)**
- Implement `Question` schema, load IPIP-NEO 120 + Holland 60 from JSON
- Curate the static 24 RIASEC subset + 30-40 IPIP/interest pool (with India-tuned rewrites)
- Implement L1.5 selection engine
- New scoring functions (RIASEC, OCEAN percentiles, Holland code, archetype cell)

**Phase 2 · Content Library (2 weeks)**
- 24 cell content files (200-500 words each, GPT-4o-assisted, manual review)
- 40 career library entries (200 words each, India-tuned)
- Rewrite IPIP-NEO 16-item interest pool in IBTI Hinglish style
- Milestone copy (4-6 lines)

**Phase 3 · Backend Endpoints + Payment (1 week)**
- Refactor assessment/payment/report routers
- Razorpay driver + mock driver
- Webhook handler + idempotency
- Short link service

**Phase 4 · Frontend Restyle (2 weeks)**
- New Tailwind theme tokens (saffron-green palette)
- Restyle landing, /start, /test, /analyzing
- New 5-screen /results layout
- /report restructure
- Auth modal + Facebook OAuth integration
- @vercel/og share image

**Phase 5 · QA + Soft Launch (1 week)**
- Internal mock-payment dry run
- Indian friend tests UPI flow live with ₹49 promo
- A/B test rarity copy
- Tighten 24 cell label phrasing based on internal feedback
- Compliance check (no caste/religion references)

**Total: ~8.5 weeks** of full-stack work for one engineer; can compress to ~5-6 weeks with parallel content authoring.

---

## 7. Out of Scope (v2+ explicit)

- Independent IBTI 31-question viral product (Option B funnel)
- Full Hindi/Tamil/Bengali/Marathi translations
- Multi-currency support
- DARU alcohol-related Easter egg
- Devanagari PDF support
- IRT calibration / L2 fully dynamic question selection
- Razorpay merchant-grade account (post company registration)
- Referral / reward mechanics on share
- Live admin dashboard for manual UPI confirmations (v1 will use SQL queries)

---

## 8. Open Questions / Risks

| # | Risk / Question | Owner | Mitigation |
|---|---|---|---|
| 1 | Razorpay personal account TPV limit ~₹50L/mo | Engineering | Track volume; upgrade to merchant pre-limit |
| 2 | Indian friend KYC reliability | Antonio | Backup A1 manual UPI confirm if KYC fails |
| 3 | 24-cell labels need cultural-fit review by Indian native | Antonio | Tier-1 city Indian friends QA before launch |
| 4 | OCEAN α coefficients with only 3 items per dim | Engineering | Acknowledge in PDF; v2 add items if α<0.55 |
| 5 | Facebook OAuth approval lead time (~1-2 weeks) | Engineering | Phase 0 pre-work |
| 6 | Hinglish in English-primary copy can confuse non-Indian visitors | Product | Footer disclaimer "Designed for Indian audience" |
| 7 | OG image rendering performance on cold start | Engineering | Vercel Edge or backend `/api/share/og` route caching |
| 8 | "MAST 0.06%" needs careful trigger logic (not pure score) | Engineering | MAST = OVERRIDE archetype when ALL conditions hold: openness ≥ 90 percentile AND extraversion ≥ 85 AND agreeableness ≥ 85 AND (1 − neuroticism) ≥ 85 AND no single RIASEC type < 40 percentile. Combined probability ≈ 0.05–0.10%. Replaces normal cell label with `MAST · The Vibing Outlier`; rest of report continues from underlying cell. |

---

## 9. Meeting Requirement Coverage (会议纪要 15 项)

| # | Requirement (会议纪要原文) | Covered in |
|---|------|------|
| 1 | 前 5 题收集基本信息，动态调整后续 | S2 §3.4–3.5 (L1.5) |
| 2 | 6 职业类型 × ≥4 题 = 24 核心 | S3 §3.7 + S2 RIASEC 24 static |
| 3 | 全卷 45 题，前职业后兴趣 | S2 §3.4 interleaved 24+16 |
| 4 | 每 10 题鼓励反馈 | S2 §3.6 milestone screens |
| 5 | MyQ 流畅 UX | S9 §3.23 + Visual Style C |
| 6 | 禁前置登录，付费时绑邮箱/WhatsApp/Google/Facebook | S7 §3.15 |
| 7 | 免费三项内容: 类型标签 / 核心洞察 / 职业方向 1-2 个 | S6 §3.13 Screens 1, 3, 4 |
| 8 | 深度 PDF: 类型标签 / 核心洞察 / 优势 / 发展建议 / 职业方向 | S4 §3.11 + Report data |
| 9 | 24 套文案库（6 类 × 状态） | S4 §3.10–3.11 (24 cells) |
| 10 | 题库本地化改写 | S2 §3.4 + S4 IPIP rewriting |
| 11 | 印度本地职业 (互联网/开发/本地常见) | S5 §3.12 (40 careers, India-tuned) |
| 12 | 优先 WhatsApp + Facebook 分享 | S8 §3.17–3.20 |
| 13 | WhatsApp 扫码支付 (UPI) | S7 §3.16 Razorpay UPI Intent |
| 14 | 微信通道内部验证 | S7 §3.16 WeChatDriver (dev mode) |
| 15 | 付费动作与登录强绑定 | S7 §3.15 Auth modal at "Unlock" |

---

## 10. Success Criteria (post-launch v1)

- ≥ 60% of visitors complete the 45 questions (drop-off < 40%)
- ≥ 35% of completers share to at least 1 channel (K factor input)
- ≥ 0.5% of completers convert to paid
- < 5% support tickets re payment confirmation issues
- ≥ NPS 8 from initial 100 paid users

---

## 11. Sources

- Meeting note (2026-04-07): "优化问卷设计与印度市场适应性讨论" — 15 requirement points
- IBTI design doc v1.0 (2026-04-18): `docs/IBTI印度市场问卷设计方案_v1.docx`
- IPIP-NEO question bank: `docs/IPIP_NEO_120_questionbank.json`
- Holland RIASEC question bank: `docs/Holland_RIASEC_60_questionbank.json`
- Style references: `https://myiq.com/zh`, `https://www.sbti.ai/en/types`

---

## End of Spec v1.0 — pending user review
