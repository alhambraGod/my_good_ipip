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

export async function startV3Assessment(
  demographic: V3DemographicAnswers
): Promise<V3StartResponse> {
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
  const r = await fetch(
    `${API_BASE}/api/v3/assessment/milestone?milestone=${milestone}&seed=${encodeURIComponent(seed)}`
  );
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

export async function verifyV3Payment(
  assessment_id: string
): Promise<{ paid: boolean; status: string }> {
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

function v3AuthHeaders(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("mindiq_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/** Associates the current JWT user with this assessment (optional; best-effort). */
export async function attachV3ProfileToAssessment(assessment_id: string): Promise<void> {
  const h = v3AuthHeaders();
  if (!h.Authorization) return;
  const r = await fetch(`${API_BASE}/api/v3/assessment/${assessment_id}/attach-profile`, {
    method: "POST",
    headers: h,
  });
  if (!r.ok) {
    /* non-fatal: user may pay as guest */
  }
}

export function getShareUrl(share_code: string): string {
  return `${API_BASE}/s/${share_code}`;
}

export function getOgImageUrl(assessment_id: string): string {
  return `${API_BASE}/api/share/${assessment_id}/og.png`;
}
