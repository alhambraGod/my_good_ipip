# CareerDNA India · Phase 4 Frontend MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the Next.js frontend to the v3 backend (Phase 3) so users can complete the full journey: landing → 5 demographic + 40 dynamic questions → milestone screens → 5-screen results → mock pay → full report → WhatsApp share. UI restyled to the C-direction "Indian saffron+green hybrid IBTI" tonality approved during brainstorming.

**MVP scope (Phase 4 ships)**:
- Saffron-green Tailwind theme tokens
- v3 API client (lib/v3-api.ts)
- Landing page restyle (印度梗 hero + diya 🪔 + saffron-green gradient)
- /test page using v3 5+40 flow with milestone screens
- /results page (5-screen scroll: label / radar / insight / careers teaser / dual CTA)
- /report page (paid-only deep view)
- Auth modal triggered at "Unlock" click (Email + WhatsApp + Google + Facebook)
- @vercel/og dynamic share image at `/api/og/[id]`
- Mock payment flow end-to-end

**Phase 4.5 follow-ups (deferred to a polish PR)**:
- Hindi locale toggle
- Real Razorpay flow live test (requires Indian friend KYC)
- Animation polish (Framer Motion timings)
- Frontend Vitest test suite
- Accessibility pass (a11y audit)
- Mobile-specific layout tuning

**Architecture:** Single Next.js 16 app. New `lib/v3-api.ts` client; old `lib/api.ts` kept for back-compat until cutover. Client components use `"use client"` directive (already the established pattern). Saffron-green theme via Tailwind 4 inline `@theme` block in `globals.css`. Auth modal as a `<dialog>`-based React component reusable across pages.

**Tech Stack:** Next.js 16.2.2, React 19, Tailwind 4, Framer Motion 12. NEW: `@vercel/og` for OG image generation.

**Spec source:** `docs/superpowers/specs/2026-04-27-careerdna-india-redesign-design.md` (S6 Result Pages, S8 Sharing, S9 UI Visual)
**Phase 3 prerequisite:** commit `fc40f5f` (161 backend tests passing, all v3 endpoints registered)

---

## Task 1: Tailwind theme + v3 API client

**Files:**
- Modify: `frontend/app/globals.css` (saffron-green theme tokens)
- Create: `frontend/lib/v3-api.ts` (typed v3 client)

- [ ] **Step 1: Update Tailwind theme tokens in `frontend/app/globals.css`**

After existing `@import "tailwindcss";` (or wherever the theme block lives), add/replace the inline `@theme` block to define saffron-green palette:

```css
@theme {
  --color-saffron-50: #FFF8EE;
  --color-saffron-100: #FFE8C7;
  --color-saffron-200: #FFD58F;
  --color-saffron-300: #FFC04A;
  --color-saffron-400: #FFA61F;
  --color-saffron-500: #FF9933;  /* Indian saffron — primary hero accent */
  --color-saffron-600: #E47A1A;
  --color-saffron-700: #B45309;  /* deep saffron — text on light */
  --color-saffron-800: #8C3F0A;
  --color-saffron-900: #5C2A07;

  --color-india-green-50: #F0F9F1;
  --color-india-green-100: #DAF1DD;
  --color-india-green-200: #C8E6C9;  /* light green — gradient mid */
  --color-india-green-300: #A0D4A8;
  --color-india-green-400: #5FB66B;
  --color-india-green-500: #138808;  /* Indian green — CTA primary */
  --color-india-green-600: #0F6E07;
  --color-india-green-700: #0A5305;
  --color-india-green-800: #064004;
  --color-india-green-900: #042B02;

  --color-cream: #FFFAF0;             /* gradient mid */
  --color-navy-text: #1A202C;         /* body text */
}

/* Indian flag–inspired hero gradient utility */
@layer utilities {
  .bg-india-hero {
    background: linear-gradient(
      140deg,
      var(--color-saffron-500) 0%,
      var(--color-saffron-200) 30%,
      var(--color-cream) 55%,
      var(--color-india-green-200) 75%,
      var(--color-india-green-500) 100%
    );
  }

  .bg-india-radial {
    background:
      radial-gradient(circle at 20% 20%, var(--color-saffron-200) 0%, transparent 40%),
      radial-gradient(circle at 80% 80%, var(--color-india-green-200) 0%, transparent 40%),
      var(--color-cream);
  }
}
```

If Tailwind 4's existing theme block already defines colors via CSS variables, merge rather than overwrite — keep `--color-indigo-*` etc. for legacy pages.

- [ ] **Step 2: Create `frontend/lib/v3-api.ts`**

```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3001";

// =========================================================================
// Types
// =========================================================================

export interface V3Question {
  id: string;
  text: string;
  instrument: "riasec" | "ipip" | "demographic" | "interest";
  response_type: "likert_5" | "single_choice" | "multi_choice";
  options: Array<{ value: string; label: string }> | null;
}

export interface V3DemographicAnswers {
  DEM_STAGE: string;
  DEM_AGE: string;
  DEM_GENDER: string;
  DEM_CITY_TIER: string;
  DEM_TOP_PRESSURE: string;
}

export interface V3StartResponse {
  assessment_id: string;
  questions: V3Question[];
  seed: string;
}

export interface V3CareerPreview {
  career_id: string;
  name_en: string;
  name_hi: string;
  tagline_en: string | null;
  salary_inr_summary: string | null;
  locked: boolean;
}

export interface V3ResultsResponse {
  assessment_id: string;
  cell_id: string;
  cell_label_en: string;
  cell_label_hi: string;
  slogan_en: string;
  rarity_pct: number;
  core_insight_en: string;
  holland_code: string;
  riasec_scores: Record<string, number>;
  holland_radar: Record<string, number>;
  careers_preview: V3CareerPreview[];
  share_code: string;
  share_url: string;
  is_paid: boolean;
  is_mast_trigger: boolean;
}

export interface V3CareerFull {
  career_id: string;
  name_en: string;
  name_hi: string;
  tagline_en: string;
  why_match: Record<string, string>;
  indian_companies: string[];
  salary_inr: { entry: string; mid: string; senior: string };
  education_path: string[];
  city_distribution: string[];
}

export interface V3ReportResponse {
  assessment_id: string;
  cell_id: string;
  cell_label_en: string;
  cell_label_hi: string;
  slogan_en: string;
  deep_description_en: string;
  strengths_en: string[];
  growth_tips_en: string[];
  ocean_scores: Record<string, number>;
  ocean_percentiles: Record<string, number>;
  holland_code: string;
  riasec_scores: Record<string, number>;
  rarity_pct: number;
  is_mast_trigger: boolean;
  careers: V3CareerFull[];
  pdf_path: string | null;
}

export interface V3PaymentIntent {
  assessment_id: string;
  provider: "mock" | "razorpay" | "wechat" | "stripe";
  payment_url: string;
  amount_inr: number;
  promo_active: boolean;
}

export interface V3MilestoneCopy {
  milestone: number;
  text: string;
}

// =========================================================================
// Endpoints
// =========================================================================

export async function getDemographicQuestions(): Promise<V3Question[]> {
  const r = await fetch(`${API_BASE}/api/v3/assessment/demographic`);
  if (!r.ok) throw new Error("Failed to fetch demographic questions");
  return r.json();
}

export async function startV3Assessment(demographic: V3DemographicAnswers): Promise<V3StartResponse> {
  const r = await fetch(`${API_BASE}/api/v3/assessment/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ demographic }),
  });
  if (!r.ok) throw new Error(`Start failed: ${r.status}`);
  return r.json();
}

export async function submitV3Assessment(
  assessment_id: string,
  answers: Record<string, number | string>
): Promise<V3ResultsResponse> {
  const r = await fetch(`${API_BASE}/api/v3/assessment/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ assessment_id, answers }),
  });
  if (!r.ok) {
    const body = await r.json().catch(() => ({}));
    throw new Error(body.detail || "Submit failed");
  }
  return r.json();
}

export async function getV3Results(assessment_id: string): Promise<V3ResultsResponse> {
  const r = await fetch(`${API_BASE}/api/v3/assessment/${assessment_id}/results`);
  if (!r.ok) throw new Error(`Get results failed: ${r.status}`);
  return r.json();
}

export async function getV3Milestone(milestone: number, seed: string): Promise<V3MilestoneCopy> {
  const r = await fetch(`${API_BASE}/api/v3/assessment/milestone?milestone=${milestone}&seed=${encodeURIComponent(seed)}`);
  if (!r.ok) throw new Error(`Milestone fetch failed: ${r.status}`);
  return r.json();
}

export async function createV3PaymentIntent(assessment_id: string): Promise<V3PaymentIntent> {
  const r = await fetch(`${API_BASE}/api/v3/payment/create-intent`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ assessment_id }),
  });
  if (!r.ok) {
    const body = await r.json().catch(() => ({}));
    throw new Error(body.detail || "Payment intent failed");
  }
  return r.json();
}

export async function verifyV3Payment(assessment_id: string): Promise<{ paid: boolean; status: string }> {
  const r = await fetch(`${API_BASE}/api/v3/payment/verify/${assessment_id}`);
  if (!r.ok) throw new Error("Verify failed");
  return r.json();
}

export async function getV3Report(assessment_id: string): Promise<V3ReportResponse> {
  const r = await fetch(`${API_BASE}/api/v3/report/${assessment_id}`);
  if (!r.ok) {
    if (r.status === 402) throw new Error("Payment required");
    throw new Error(`Report fetch failed: ${r.status}`);
  }
  return r.json();
}

export function getShareUrl(share_code: string): string {
  return `${API_BASE}/s/${share_code}`;
}

export function getOgImageUrl(assessment_id: string): string {
  return `${API_BASE}/api/share/${assessment_id}/og.png`;
}
```

- [ ] **Step 3: Verify build + commit**

```bash
cd /Users/antonio/god/my_good_ipip/frontend && npm run build 2>&1 | tail -20
```

If build fails, fix TypeScript errors. Otherwise:

```bash
cd /Users/antonio/god/my_good_ipip && git add frontend/app/globals.css frontend/lib/v3-api.ts
git commit -m "feat(frontend): add saffron-green Tailwind theme + v3 API client"
```

---

## Task 2: Landing page restyle (Indian hero)

**Files:**
- Modify: `frontend/app/page.tsx`

- [ ] **Step 1: Replace landing page content**

```tsx
"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

export default function LandingPage() {
  const [stats, setStats] = useState({ total_assessments: 1247, today_assessments: 47 });

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:3001"}/api/stats`)
      .then((r) => r.json())
      .then(setStats)
      .catch(() => {});
  }, []);

  return (
    <main className="flex flex-col min-h-screen">
      {/* Hero */}
      <section className="bg-india-hero px-6 py-20 md:py-28 text-center relative overflow-hidden">
        <div className="absolute top-6 left-6 text-3xl">🪔</div>
        <div className="relative z-10 max-w-3xl mx-auto">
          <div className="text-xs font-semibold tracking-[0.25em] uppercase text-saffron-700 mb-4">
            Indian-built personality + career mapping
          </div>
          <h1 className="text-4xl md:text-6xl font-bold leading-tight mb-6 text-navy-text">
            Find Your <br />
            <span className="bg-clip-text text-transparent bg-gradient-to-br from-saffron-700 to-india-green-500">
              Indian Career DNA
            </span>
          </h1>
          <p className="text-lg md:text-xl text-navy-text/80 mb-8 max-w-2xl mx-auto">
            45 questions. 5 minutes. Built on Holland RIASEC + Big Five (OCEAN). Tuned for Indian Gen-Z reality —
            Bangalore IT, Marwari hustle, Sharma ji&apos;s beta, EMI math, all of it.
          </p>
          <Link
            href="/test"
            className="inline-block bg-india-green-500 hover:bg-india-green-600 text-white font-bold text-lg px-10 py-4 rounded-full transition-all shadow-lg hover:shadow-xl hover:scale-105"
          >
            Start Free Test →
          </Link>
          <p className="mt-6 text-saffron-800 text-sm font-medium">
            {stats.today_assessments.toLocaleString()}+ Indians took the test today · No login needed to start
          </p>
        </div>
      </section>

      {/* What you get */}
      <section className="bg-cream px-6 py-16">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12 text-navy-text">
            What you get
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                emoji: "🎯",
                title: "Your archetype",
                desc: "One of 24 hand-curated Indian personality cells (e.g., The 3AM Chai Philosopher). Built on Holland's hexagon theory + IBTI Indian context.",
              },
              {
                emoji: "💼",
                title: "Career match",
                desc: "5+ Indian career paths matched to your archetype, with real companies (Razorpay, Swiggy, TCS, Marwari business families) and lakh-based salary ranges.",
              },
              {
                emoji: "📤",
                title: "WhatsApp-ready share",
                desc: "Pre-written share lines + share image so your friends can take the test and find their archetype.",
              },
            ].map((f) => (
              <div
                key={f.title}
                className="bg-white rounded-2xl p-8 border border-saffron-200/50 hover:shadow-xl transition-shadow"
              >
                <div className="text-4xl mb-4">{f.emoji}</div>
                <h3 className="text-xl font-semibold mb-3 text-navy-text">
                  {f.title}
                </h3>
                <p className="text-navy-text/70 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-gradient-to-br from-india-green-500 to-india-green-700 text-white py-16 px-6 text-center">
        <h2 className="text-3xl font-bold mb-4">
          Ready to find your archetype?
        </h2>
        <p className="text-india-green-50 mb-8 max-w-lg mx-auto">
          5 minutes. No login. ₹49 if you want the full report (first 1,000 users).
        </p>
        <Link
          href="/test"
          className="inline-block bg-white text-india-green-700 font-bold text-lg px-10 py-4 rounded-full hover:bg-saffron-50 transition-all shadow-lg"
        >
          Start Now
        </Link>
      </section>

      {/* Footer */}
      <footer className="bg-navy-text text-saffron-100/60 py-8 px-6 text-center text-sm">
        <p>&copy; 2026 CareerDNA · For Indian Gen-Z, by Indians.</p>
        <p className="mt-1 text-saffron-100/40">
          Built on IPIP-NEO Big Five + Holland RIASEC personality science.
        </p>
      </footer>
    </main>
  );
}
```

- [ ] **Step 2: Verify build + commit**

```bash
cd /Users/antonio/god/my_good_ipip/frontend && npm run build 2>&1 | tail -15
```

```bash
cd /Users/antonio/god/my_good_ipip && git add frontend/app/page.tsx
git commit -m "feat(frontend): restyle landing page with India hero (saffron-green + Hinglish copy)"
```

---

## Task 3: /test page with v3 5+40 flow + milestone screens

**Files:**
- Modify: `frontend/app/test/page.tsx` (rewrite using v3 API)

- [ ] **Step 1: Replace `frontend/app/test/page.tsx`**

```tsx
"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  getDemographicQuestions,
  startV3Assessment,
  submitV3Assessment,
  getV3Milestone,
  type V3Question,
  type V3DemographicAnswers,
} from "@/lib/v3-api";

const LIKERT_OPTIONS = [
  { value: 1, label: "Strongly Disagree" },
  { value: 2, label: "Disagree" },
  { value: 3, label: "Neutral" },
  { value: 4, label: "Agree" },
  { value: 5, label: "Strongly Agree" },
];

const MILESTONE_THRESHOLDS = [10, 20, 30, 40];

type Phase = "loading" | "demographic" | "main" | "milestone" | "submitting";

export default function TestPage() {
  const router = useRouter();
  const [phase, setPhase] = useState<Phase>("loading");
  const [demographicQs, setDemographicQs] = useState<V3Question[]>([]);
  const [demographicAnswers, setDemographicAnswers] = useState<Partial<V3DemographicAnswers>>({});
  const [demographicIdx, setDemographicIdx] = useState(0);

  const [assessmentId, setAssessmentId] = useState<string | null>(null);
  const [seed, setSeed] = useState<string>("");
  const [mainQs, setMainQs] = useState<V3Question[]>([]);
  const [mainIdx, setMainIdx] = useState(0);
  const [answers, setAnswers] = useState<Record<string, number>>({});

  const [milestoneText, setMilestoneText] = useState<string>("");
  const [pendingMilestone, setPendingMilestone] = useState<number | null>(null);

  // Load demographic questions
  useEffect(() => {
    getDemographicQuestions()
      .then((qs) => {
        setDemographicQs(qs);
        setPhase("demographic");
      })
      .catch(() => router.push("/"));
  }, [router]);

  // Demographic answer handler
  const handleDemographicAnswer = (questionId: string, value: string) => {
    const updated = { ...demographicAnswers, [questionId]: value };
    setDemographicAnswers(updated);
    if (demographicIdx + 1 < demographicQs.length) {
      setDemographicIdx(demographicIdx + 1);
    } else {
      // All 5 answered → call /start
      void startMainPhase(updated as V3DemographicAnswers);
    }
  };

  const startMainPhase = useCallback(async (dem: V3DemographicAnswers) => {
    setPhase("loading");
    try {
      const start = await startV3Assessment(dem);
      setAssessmentId(start.assessment_id);
      setSeed(start.seed);
      setMainQs(start.questions);
      setPhase("main");
    } catch (e) {
      console.error(e);
      router.push("/");
    }
  }, [router]);

  // Main answer handler
  const handleMainAnswer = (questionId: string, value: number) => {
    const updated = { ...answers, [questionId]: value };
    setAnswers(updated);

    const totalAnswered = Object.keys(updated).length;
    const milestone = MILESTONE_THRESHOLDS.find((m) => m === totalAnswered);

    if (milestone) {
      // Trigger milestone screen
      void showMilestone(milestone);
      return;
    }

    if (mainIdx + 1 < mainQs.length) {
      setMainIdx(mainIdx + 1);
    } else {
      void submitAnswers(updated);
    }
  };

  const showMilestone = useCallback(async (m: number) => {
    setPhase("milestone");
    setPendingMilestone(m);
    try {
      const res = await getV3Milestone(m, seed);
      setMilestoneText(res.text);
    } catch {
      setMilestoneText("Keep going!");
    }
  }, [seed]);

  const continueAfterMilestone = () => {
    setPhase("main");
    setPendingMilestone(null);
    if (mainIdx + 1 < mainQs.length) {
      setMainIdx(mainIdx + 1);
    } else {
      void submitAnswers(answers);
    }
  };

  const submitAnswers = useCallback(async (allAnswers: Record<string, number>) => {
    if (!assessmentId) return;
    setPhase("submitting");
    try {
      await submitV3Assessment(assessmentId, allAnswers);
      router.push(`/results/${assessmentId}`);
    } catch (e) {
      console.error(e);
      alert("Failed to submit. Please try again.");
      setPhase("main");
    }
  }, [assessmentId, router]);

  // Render phases
  if (phase === "loading") {
    return (
      <div className="min-h-screen bg-india-radial flex items-center justify-center">
        <p className="text-navy-text/70">🪔 Loading…</p>
      </div>
    );
  }

  if (phase === "demographic") {
    const q = demographicQs[demographicIdx];
    if (!q) return null;
    const progress = ((demographicIdx + 1) / 5) * 100;
    return (
      <main className="min-h-screen bg-india-radial flex flex-col">
        <div className="h-2 bg-saffron-100">
          <div
            className="h-full bg-gradient-to-r from-saffron-500 to-india-green-500 transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="flex-1 flex items-center justify-center px-6 py-12">
          <div className="max-w-xl w-full">
            <div className="text-saffron-700 text-xs font-semibold uppercase tracking-widest mb-3">
              Question {demographicIdx + 1} of 5 · Quick start
            </div>
            <h2 className="text-2xl md:text-3xl font-bold text-navy-text mb-8">{q.text}</h2>
            <div className="grid gap-3">
              {q.options?.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => handleDemographicAnswer(q.id, opt.value)}
                  className="text-left px-6 py-4 bg-white rounded-2xl border-2 border-saffron-200 hover:border-india-green-400 hover:bg-india-green-50 transition-all font-medium text-navy-text"
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </main>
    );
  }

  if (phase === "milestone") {
    const m = pendingMilestone ?? 0;
    return (
      <main className="min-h-screen bg-india-hero flex flex-col items-center justify-center px-6 text-center">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="max-w-md"
        >
          <div className="text-6xl mb-6">🪔</div>
          <div className="text-7xl font-bold text-saffron-700 mb-4">{m}</div>
          <p className="text-xl text-navy-text font-medium mb-8">{milestoneText || "Keep going!"}</p>
          <button
            onClick={continueAfterMilestone}
            className="bg-india-green-500 hover:bg-india-green-600 text-white font-bold px-8 py-3 rounded-full transition-all shadow-lg"
          >
            Continue
          </button>
        </motion.div>
      </main>
    );
  }

  if (phase === "main") {
    const q = mainQs[mainIdx];
    if (!q) return null;
    const progress = (5 + mainIdx + 1) / 45 * 100;
    return (
      <main className="min-h-screen bg-india-radial flex flex-col">
        <div className="h-2 bg-saffron-100">
          <div
            className="h-full bg-gradient-to-r from-saffron-500 to-india-green-500 transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="flex-1 flex items-center justify-center px-6 py-12">
          <AnimatePresence mode="wait">
            <motion.div
              key={mainIdx}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="max-w-xl w-full"
            >
              <div className="text-saffron-700 text-xs font-semibold uppercase tracking-widest mb-3">
                Question {5 + mainIdx + 1} of 45
              </div>
              <h2 className="text-xl md:text-2xl font-medium text-navy-text mb-8">{q.text}</h2>
              <div className="grid gap-2">
                {LIKERT_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => handleMainAnswer(q.id, opt.value)}
                    className="text-left px-6 py-3 bg-white rounded-xl border-2 border-saffron-200 hover:border-india-green-400 hover:bg-india-green-50 transition-all font-medium text-navy-text"
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
    );
  }

  return (
    <div className="min-h-screen bg-india-radial flex items-center justify-center">
      <motion.div animate={{ rotate: 360 }} transition={{ duration: 2, repeat: Infinity, ease: "linear" }} className="text-5xl">
        🪔
      </motion.div>
      <p className="ml-4 text-navy-text font-medium">Decoding your archetype…</p>
    </div>
  );
}
```

- [ ] **Step 2: Verify build + commit**

```bash
cd /Users/antonio/god/my_good_ipip/frontend && npm run build 2>&1 | tail -15
```

If build fails on `framer-motion` import or React 19 + Next 16 quirks, debug per error.

```bash
cd /Users/antonio/god/my_good_ipip && git add frontend/app/test/page.tsx
git commit -m "feat(frontend): rewrite /test page with v3 5+40 flow + milestone screens"
```

---

## Task 4: /results page with 5-screen scroll layout

**Files:**
- Create: `frontend/app/results/[id]/page.tsx` (new dynamic route — old `/results?id=` deprecated)

NOTE: Old `frontend/app/results/page.tsx` (query-string based) keeps working for backward compat. New route at `/results/[id]` is what /test redirects to.

- [ ] **Step 1: Create dynamic results route**

`frontend/app/results/[id]/page.tsx`:

```tsx
"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  getV3Results,
  type V3ResultsResponse,
  type V3CareerPreview,
} from "@/lib/v3-api";

const RIASEC_LABELS: Record<string, string> = {
  R: "Realistic", I: "Investigative", A: "Artistic",
  S: "Social", E: "Enterprising", C: "Conventional",
};

export default function ResultsPage() {
  const params = useParams();
  const router = useRouter();
  const assessmentId = params?.id as string | undefined;
  const [data, setData] = useState<V3ResultsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!assessmentId) {
      router.push("/");
      return;
    }
    getV3Results(assessmentId)
      .then(setData)
      .catch(() => router.push("/"))
      .finally(() => setLoading(false));
  }, [assessmentId, router]);

  if (loading || !data) {
    return (
      <main className="min-h-screen bg-india-radial flex items-center justify-center">
        <p className="text-navy-text/70">Loading…</p>
      </main>
    );
  }

  return (
    <main className="bg-cream">
      {/* Screen 1: Personality Card */}
      <section className="bg-india-hero min-h-screen flex flex-col items-center justify-center px-6 py-16 text-center relative">
        <div className="absolute top-6 left-6 text-3xl">🪔</div>
        <div className="absolute top-6 right-6 text-xs font-bold bg-white/70 backdrop-blur px-3 py-1 rounded-full text-saffron-700 border border-saffron-700/30">
          RARE {data.rarity_pct}%
        </div>
        <motion.div
          initial={{ scale: 0.5, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.6 }}
        >
          <div className="text-saffron-700 text-xs font-bold tracking-[0.3em] uppercase mb-3">
            Your Personality Code
          </div>
          <div className="text-8xl md:text-9xl font-black bg-clip-text text-transparent bg-gradient-to-br from-navy-text to-saffron-700 mb-2">
            {data.cell_id}
          </div>
          <div className="text-2xl md:text-3xl font-bold text-navy-text mb-3">
            {data.cell_label_en}
          </div>
          <p className="text-lg text-navy-text/80 italic max-w-md mx-auto bg-white/60 backdrop-blur p-4 rounded-2xl">
            &ldquo;{data.slogan_en}&rdquo;
          </p>
          <p className="text-sm text-india-green-700 font-bold mt-4">
            ★ You&apos;re {data.rarity_pct}% of Indian Gen Z ★
          </p>
        </motion.div>
        <ShareButton shareUrl={data.share_url} text={`I'm ${data.cell_id}. ${data.slogan_en} Try the test → ${data.share_url}`} />
      </section>

      {/* Screen 2: Holland Radar */}
      <section className="min-h-screen flex flex-col items-center justify-center px-6 py-16 bg-cream">
        <div className="max-w-md w-full">
          <h2 className="text-2xl font-bold text-navy-text text-center mb-6">Holland Radar</h2>
          <RadarChart scores={data.holland_radar} />
          <p className="text-navy-text/70 text-center mt-6">
            <strong>{data.holland_code[0]}</strong>-dominant + <strong>{data.holland_code[1]}</strong>-supporting
          </p>
        </div>
      </section>

      {/* Screen 3: Core Insight */}
      <section className="min-h-screen flex flex-col items-center justify-center px-6 py-16 bg-india-radial">
        <div className="max-w-2xl">
          <h2 className="text-saffron-700 text-xs font-bold tracking-widest uppercase mb-4 text-center">
            Core Insight
          </h2>
          <p className="text-lg md:text-xl text-navy-text leading-relaxed bg-white/80 backdrop-blur p-8 rounded-3xl shadow-lg">
            {data.core_insight_en}
          </p>
        </div>
      </section>

      {/* Screen 4: Careers Teaser */}
      <section className="min-h-screen flex flex-col items-center justify-center px-6 py-16 bg-cream">
        <div className="max-w-2xl w-full">
          <h2 className="text-2xl font-bold text-navy-text text-center mb-8">Career Paths</h2>
          <div className="space-y-4">
            {data.careers_preview.map((career, i) => (
              <CareerCard key={career.career_id} career={career} index={i} />
            ))}
          </div>
        </div>
      </section>

      {/* Screen 5: Dual CTA */}
      <section className="bg-gradient-to-br from-india-green-500 to-india-green-700 text-white py-16 px-6 text-center">
        <h2 className="text-3xl font-bold mb-4">Want the full report?</h2>
        <p className="text-india-green-50 mb-8 max-w-md mx-auto">
          Unlock all 5+ careers, OCEAN analysis, strengths, growth tips, and PDF download.
        </p>
        <div className="flex flex-col md:flex-row gap-4 max-w-md mx-auto">
          <ShareButton
            shareUrl={data.share_url}
            text={`I'm ${data.cell_id}. ${data.slogan_en} → ${data.share_url}`}
            variant="white-outline"
          />
          <Link
            href={`/payment?assessment_id=${data.assessment_id}`}
            className="flex-1 bg-saffron-500 hover:bg-saffron-600 text-navy-text font-bold py-3 px-6 rounded-full transition-all shadow-lg"
          >
            Unlock ₹49 →
          </Link>
        </div>
      </section>
    </main>
  );
}

function ShareButton({ shareUrl, text, variant = "default" }: { shareUrl: string; text: string; variant?: string }) {
  const handleShare = async () => {
    if (typeof navigator !== "undefined" && navigator.share) {
      try {
        await navigator.share({ text, url: shareUrl });
        return;
      } catch {}
    }
    const wa = `https://wa.me/?text=${encodeURIComponent(text)}`;
    window.open(wa, "_blank");
  };
  const cls = variant === "white-outline"
    ? "flex-1 bg-white/10 border border-white text-white font-bold py-3 px-6 rounded-full hover:bg-white/20 transition-all"
    : "mt-8 bg-india-green-500 hover:bg-india-green-600 text-white font-bold px-6 py-3 rounded-full transition-all shadow-lg";
  return <button onClick={handleShare} className={cls}>📤 Share to WhatsApp</button>;
}

function CareerCard({ career, index }: { career: V3CareerPreview; index: number }) {
  if (career.locked) {
    return (
      <div className="bg-white/60 border-2 border-saffron-200/50 rounded-2xl p-6 backdrop-blur">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🔒</span>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-navy-text/50">{career.name_en}</h3>
            <p className="text-navy-text/40 text-sm">Unlock to see this career&apos;s deep dive.</p>
          </div>
        </div>
      </div>
    );
  }
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      className="bg-white border-2 border-india-green-300 rounded-2xl p-6 shadow-lg"
    >
      <div className="text-saffron-700 text-xs font-bold uppercase tracking-widest mb-2">Top match</div>
      <h3 className="text-2xl font-bold text-navy-text mb-2">{career.name_en}</h3>
      <p className="text-navy-text/70 mb-3">{career.tagline_en}</p>
      <div className="text-india-green-700 text-sm font-bold">{career.salary_inr_summary}</div>
    </motion.div>
  );
}

function RadarChart({ scores }: { scores: Record<string, number> }) {
  // Simple SVG hex chart for 6 RIASEC types
  const types = ["R", "I", "A", "S", "E", "C"];
  const max = 20;
  const cx = 100;
  const cy = 100;
  const r = 80;
  const points = types.map((t, i) => {
    const angle = (i * Math.PI / 3) - Math.PI / 2;
    const score = scores[t] ?? 0;
    const ratio = score / max;
    return [cx + Math.cos(angle) * r * ratio, cy + Math.sin(angle) * r * ratio];
  });
  const grid = [0.25, 0.5, 0.75, 1.0].map((g) => {
    const gridPoints = types.map((_, i) => {
      const angle = (i * Math.PI / 3) - Math.PI / 2;
      return [cx + Math.cos(angle) * r * g, cy + Math.sin(angle) * r * g];
    });
    return gridPoints.map(([x, y]) => `${x},${y}`).join(" ");
  });
  return (
    <svg viewBox="0 0 200 200" className="w-full">
      {grid.map((pts, i) => (
        <polygon key={i} points={pts} fill="none" stroke="#FFD58F" strokeWidth="0.5" />
      ))}
      <polygon
        points={points.map(([x, y]) => `${x},${y}`).join(" ")}
        fill="rgba(255, 153, 51, 0.3)"
        stroke="#FF9933"
        strokeWidth="2"
      />
      {types.map((t, i) => {
        const angle = (i * Math.PI / 3) - Math.PI / 2;
        return (
          <text
            key={t}
            x={cx + Math.cos(angle) * (r + 10)}
            y={cy + Math.sin(angle) * (r + 10)}
            textAnchor="middle"
            fill="#1A202C"
            fontSize="10"
            fontWeight="bold"
            dy="3"
          >
            {RIASEC_LABELS[t][0]}
          </text>
        );
      })}
    </svg>
  );
}
```

- [ ] **Step 2: Build + commit**

```bash
cd /Users/antonio/god/my_good_ipip/frontend && npm run build 2>&1 | tail -15
```

```bash
cd /Users/antonio/god/my_good_ipip && git add frontend/app/results/
git commit -m "feat(frontend): add /results/[id] with 5-screen scroll layout (label/radar/insight/careers/CTA)"
```

---

## Task 5: /payment + /report pages (mock flow)

**Files:**
- Create: `frontend/app/payment/page.tsx` (replace existing)
- Create: `frontend/app/report/[id]/page.tsx` (replace existing)

- [ ] **Step 1: Replace `frontend/app/payment/page.tsx`**

```tsx
"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { createV3PaymentIntent, verifyV3Payment } from "@/lib/v3-api";

function PaymentContent() {
  const router = useRouter();
  const sp = useSearchParams();
  const assessmentId = sp.get("assessment_id");
  const mockSuccess = sp.get("mock") === "true";

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!assessmentId) {
      router.push("/");
      return;
    }
    if (mockSuccess) {
      // Mock success path: verify + redirect to report
      verifyV3Payment(assessmentId)
        .then(() => router.push(`/report/${assessmentId}`))
        .catch((e) => setError(String(e)))
        .finally(() => setLoading(false));
      return;
    }
    // Create intent and redirect to payment URL
    createV3PaymentIntent(assessmentId)
      .then((intent) => {
        // For mock provider, intent.payment_url already contains ?mock=true
        window.location.href = intent.payment_url;
      })
      .catch((e) => {
        setError(String(e));
        setLoading(false);
      });
  }, [assessmentId, mockSuccess, router]);

  if (error) {
    return (
      <main className="min-h-screen bg-india-radial flex items-center justify-center px-6">
        <div className="bg-white rounded-2xl p-8 max-w-md text-center">
          <h2 className="text-xl font-bold text-navy-text mb-2">Payment error</h2>
          <p className="text-navy-text/70 mb-4">{error}</p>
          <button onClick={() => router.back()} className="text-india-green-700 underline">Go back</button>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-india-radial flex items-center justify-center">
      <p className="text-navy-text/70">{loading ? "Setting up payment…" : "Redirecting…"}</p>
    </main>
  );
}

export default function PaymentPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-india-radial flex items-center justify-center"><p>Loading…</p></div>}>
      <PaymentContent />
    </Suspense>
  );
}
```

- [ ] **Step 2: Replace `frontend/app/report/[id]/page.tsx`**

```tsx
"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { getV3Report, type V3ReportResponse } from "@/lib/v3-api";

const OCEAN_LABELS: Record<string, string> = {
  openness: "Openness", conscientiousness: "Conscientiousness",
  extraversion: "Extraversion", agreeableness: "Agreeableness",
  neuroticism: "Neuroticism (lower = more emotionally stable)",
};

export default function ReportPage() {
  const params = useParams();
  const router = useRouter();
  const assessmentId = params?.id as string | undefined;
  const [report, setReport] = useState<V3ReportResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!assessmentId) { router.push("/"); return; }
    getV3Report(assessmentId)
      .then(setReport)
      .catch((e) => {
        setError(String(e));
        if (String(e).includes("Payment required")) router.push(`/results/${assessmentId}`);
      });
  }, [assessmentId, router]);

  if (error && !error.includes("Payment required")) {
    return (
      <main className="min-h-screen bg-india-radial flex items-center justify-center px-6">
        <div className="bg-white rounded-2xl p-8 max-w-md text-center">
          <h2 className="text-xl font-bold text-navy-text mb-2">Couldn&apos;t load report</h2>
          <p className="text-navy-text/70 mb-4">{error}</p>
          <Link href="/" className="text-india-green-700 underline">Home</Link>
        </div>
      </main>
    );
  }

  if (!report) {
    return <main className="min-h-screen bg-india-radial flex items-center justify-center"><p>Loading…</p></main>;
  }

  return (
    <main className="bg-cream pb-16">
      <section className="bg-india-hero py-16 px-6 text-center">
        <div className="text-saffron-700 text-xs font-bold tracking-widest uppercase mb-3">
          Your Full Report
        </div>
        <div className="text-7xl font-black text-navy-text mb-2">{report.cell_id}</div>
        <div className="text-2xl font-bold text-navy-text mb-2">{report.cell_label_en}</div>
        <p className="text-navy-text/80 italic">&ldquo;{report.slogan_en}&rdquo;</p>
      </section>

      <section className="max-w-3xl mx-auto px-6 py-12 space-y-12">
        {/* Deep description */}
        <div>
          <h2 className="text-2xl font-bold text-navy-text mb-4">Who you are</h2>
          <p className="text-navy-text/80 leading-relaxed whitespace-pre-line">{report.deep_description_en}</p>
        </div>

        {/* Strengths */}
        <div>
          <h2 className="text-2xl font-bold text-navy-text mb-4">Your strengths</h2>
          <ul className="space-y-3">
            {report.strengths_en.map((s, i) => (
              <li key={i} className="flex gap-3 bg-white rounded-xl p-4 border-l-4 border-india-green-500">
                <span className="text-india-green-500 font-bold">{i + 1}.</span>
                <span className="text-navy-text">{s}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Growth tips */}
        <div>
          <h2 className="text-2xl font-bold text-navy-text mb-4">Growth tips</h2>
          <ul className="space-y-3">
            {report.growth_tips_en.map((t, i) => (
              <li key={i} className="flex gap-3 bg-saffron-50 rounded-xl p-4 border-l-4 border-saffron-500">
                <span className="text-saffron-700 font-bold">{i + 1}.</span>
                <span className="text-navy-text">{t}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* OCEAN */}
        <div>
          <h2 className="text-2xl font-bold text-navy-text mb-4">OCEAN scores</h2>
          <div className="space-y-3">
            {Object.entries(report.ocean_percentiles).map(([dim, pct]) => (
              <div key={dim}>
                <div className="flex justify-between text-sm font-medium text-navy-text mb-1">
                  <span>{OCEAN_LABELS[dim] ?? dim}</span>
                  <span>{pct}%</span>
                </div>
                <div className="h-2 bg-saffron-100 rounded-full">
                  <div
                    className="h-full bg-gradient-to-r from-saffron-500 to-india-green-500 rounded-full transition-all"
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Careers */}
        <div>
          <h2 className="text-2xl font-bold text-navy-text mb-6">Career paths</h2>
          <div className="space-y-6">
            {report.careers.map((c) => (
              <div key={c.career_id} className="bg-white rounded-2xl p-6 shadow border-l-4 border-india-green-500">
                <h3 className="text-xl font-bold text-navy-text mb-1">{c.name_en}</h3>
                <p className="text-navy-text/70 italic mb-3">{c.tagline_en}</p>
                {c.why_match[report.cell_id] && (
                  <div className="bg-india-green-50 rounded-xl p-4 mb-4">
                    <div className="text-india-green-700 text-xs font-bold uppercase tracking-widest mb-1">
                      Why this fits you
                    </div>
                    <p className="text-navy-text/80">{c.why_match[report.cell_id]}</p>
                  </div>
                )}
                <div className="grid md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <div className="text-saffron-700 font-bold">Indian companies</div>
                    <div className="text-navy-text/80">{c.indian_companies.join(" · ")}</div>
                  </div>
                  <div>
                    <div className="text-saffron-700 font-bold">Salary (INR)</div>
                    <div className="text-navy-text/80">
                      Entry {c.salary_inr.entry} · Mid {c.salary_inr.mid} · Senior {c.salary_inr.senior}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
```

- [ ] **Step 3: Build + commit**

```bash
cd /Users/antonio/god/my_good_ipip/frontend && npm run build 2>&1 | tail -15
```

```bash
cd /Users/antonio/god/my_good_ipip && git add frontend/app/payment/ frontend/app/report/
git commit -m "feat(frontend): add v3 payment redirect + /report/[id] full report page"
```

---

## Task 6: Smoke E2E (manual or automated)

**Files:**
- Create: `frontend/scripts/smoke-test.sh` (optional manual smoke runner)

- [ ] **Step 1: Smoke test (manual is OK for MVP)**

Backend should be running (`bash backend/deploy_backend.sh dev`). Frontend dev server (`bash frontend/deploy_frontend.sh dev`). Visit `http://localhost:3000` and walk through:

1. Landing → click "Start Free Test"
2. /test → answer 5 demographic Qs (any options)
3. /test → answer 40 main Qs (any likert)
4. Milestone screens at Q10/Q20/Q30/Q40 should appear
5. After Q45, redirect to /results/[id]
6. /results/[id] → 5 sections render correctly
7. Click "Unlock ₹49 →" → /payment?assessment_id=...
8. Mock flow auto-redirects to /payment/success?mock=true
9. /payment redirects to /report/[id]
10. /report/[id] → full report renders

If any step fails, debug.

- [ ] **Step 2: Commit (no code changes for manual smoke; this step ensures phase is closed)**

If everything works, mark Phase 4 complete with a summary commit:

```bash
cd /Users/antonio/god/my_good_ipip && git commit --allow-empty -m "chore(frontend): Phase 4 MVP frontend smoke test passing"
```

---

## Phase 4 Acceptance Criteria

- [ ] `cd frontend && npm run build` succeeds (no TypeScript / ESLint errors)
- [ ] Landing page renders with saffron-green hero
- [ ] /test page completes 5 demographic + 40 dynamic questions with milestone screens
- [ ] /results/[id] renders 5 sections (label / radar / insight / careers / CTA)
- [ ] Mock payment flow ends at /report/[id] showing full report
- [ ] WhatsApp share button opens wa.me with prefilled text
- [ ] Conventional commit messages

---

## Phase 4 → Spec Coverage

- ✅ S6 §3.13–3.14 Result page IA — Tasks 4
- ✅ S8 §3.17–3.20 Sharing — Task 4 (share buttons), Task 7 future enhancement (@vercel/og)
- ✅ S9 §3.21–3.23 UI Visual — Tasks 1, 2, 3, 4, 5
- ⏭ Auth modal + Facebook OAuth integration — Phase 4.5
- ⏭ @vercel/og dynamic share images — Phase 4.5 (backend stub returns placeholder for now)
- ⏭ Hindi locale toggle — v2

---

## Estimated Effort

~6-8 hours for one engineer (TypeScript + React + Tailwind 4). Backend integration is straightforward — Phase 3 v3 API is well-typed.

---

## Phase 4 — IN PROGRESS

Plan saved. Execution proceeds via subagent-driven development.
