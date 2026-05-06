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
  is_preview?: boolean;       // true when shown to an unpaid assessment in dev
}

export interface V3PaymentIntent {
  assessment_id: string;
  provider: "mock" | "razorpay" | "cashfree" | "payu" | "upi" | "wechat" | "stripe";
  payment_url: string;
  amount_inr: number;
  promo_active: boolean;
  txn_id?: string | null;
  client_payload?: Record<string, unknown> | null;
  qr_code_data_url?: string | null;
}

export interface V3MilestoneCopy {
  milestone: number;
  text: string;
}

export interface V3PriceInfo {
  amount_inr: number;
  promo_active: boolean;
  promo_remaining: number;
  price_full_inr: number;
  price_promo_inr: number;
  promo_cap: number;
}

export interface V3ArchetypeSummary {
  cell_id: string;
  label_en: string;
  label_hi: string;
  slogan_en: string;
  rarity_pct: number;
}

export interface V3ArchetypeDetail extends V3ArchetypeSummary {
  core_insight_en: string;
  deep_description_en: string;
  strengths_en: string[];
  growth_tips_en: string[];
  career_directions: string[];
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

export async function getV3AssessmentState(
  assessment_id: string
): Promise<V3StartResponse> {
  const r = await fetch(`${API_BASE}/api/v3/assessment/${assessment_id}/state`);
  if (!r.ok) throw new Error(`State fetch failed: ${r.status}`);
  return r.json();
}

export async function getV3Price(): Promise<V3PriceInfo> {
  const r = await fetch(`${API_BASE}/api/v3/payment/price`);
  if (!r.ok) throw new Error("Price fetch failed");
  return r.json();
}

export interface V3RazorpayOrder {
  assessment_id: string;
  provider: "razorpay" | "mock";
  order_id: string | null;
  amount_inr: number;
  amount_paise: number;
  currency: string;
  key_id: string | null;
  promo_active: boolean;
  mock_redirect_url: string | null;
}

export async function createV3RazorpayOrder(assessment_id: string): Promise<V3RazorpayOrder> {
  const r = await fetch(`${API_BASE}/api/v3/payment/razorpay/order`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ assessment_id }),
  });
  if (!r.ok) {
    const body = await r.json().catch(() => ({}));
    throw new Error(body.detail || "Razorpay order failed");
  }
  return r.json();
}

export async function verifyV3RazorpayCheckout(payload: {
  assessment_id: string;
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
}): Promise<{ assessment_id: string; paid: boolean; status: string }> {
  const r = await fetch(`${API_BASE}/api/v3/payment/razorpay/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!r.ok) {
    const body = await r.json().catch(() => ({}));
    throw new Error(body.detail || "Razorpay verify failed");
  }
  return r.json();
}

export async function listArchetypes(): Promise<V3ArchetypeSummary[]> {
  const r = await fetch(`${API_BASE}/api/v3/archetypes`, { next: { revalidate: 600 } });
  if (!r.ok) throw new Error("Archetype list failed");
  return r.json();
}

export async function getArchetypeDetail(cellId: string): Promise<V3ArchetypeDetail> {
  const r = await fetch(`${API_BASE}/api/v3/archetypes/${cellId}`, {
    next: { revalidate: 600 },
  });
  if (!r.ok) {
    if (r.status === 404) throw new Error("Archetype not found");
    throw new Error("Archetype fetch failed");
  }
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

export async function getV3Milestone(
  milestone: number,
  seed: string,
  lang: "en" | "hi" = "en",
): Promise<V3MilestoneCopy> {
  const params = new URLSearchParams({
    milestone: String(milestone),
    seed,
    lang,
  });
  const r = await fetch(`${API_BASE}/api/v3/assessment/milestone?${params}`);
  if (!r.ok) throw new Error(`Milestone fetch failed: ${r.status}`);
  return r.json();
}

export async function createV3PaymentIntent(
  assessment_id: string,
  provider?: string,
): Promise<V3PaymentIntent> {
  const r = await fetch(`${API_BASE}/api/v3/payment/create-intent`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ assessment_id, provider }),
  });
  if (!r.ok) {
    const body = await r.json().catch(() => ({}));
    throw new Error(body.detail || "Payment intent failed");
  }
  return r.json();
}

export interface V3PaymentProvider {
  id: "mock" | "razorpay" | "cashfree" | "payu" | "upi" | "stripe";
  label_en: string;
  label_hi: string;
  description_en: string;
  supports_methods: string[];
  requires_redirect: boolean;
  recommended: boolean;
  enabled: boolean;
}

export interface V3PaymentProvidersResponse {
  default: string;
  providers: V3PaymentProvider[];
}

export async function getV3PaymentProviders(): Promise<V3PaymentProvidersResponse> {
  const r = await fetch(`${API_BASE}/api/v3/payment/providers`);
  if (!r.ok) throw new Error("Providers fetch failed");
  return r.json();
}

export async function confirmV3UPIPayment(payload: {
  assessment_id: string;
  txn_ref?: string;
  user_remark?: string;
}): Promise<{ assessment_id: string; paid: boolean; status: string; message?: string }> {
  const r = await fetch(`${API_BASE}/api/v3/payment/upi/confirm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!r.ok) {
    const body = await r.json().catch(() => ({}));
    throw new Error(body.detail || "UPI confirm failed");
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
