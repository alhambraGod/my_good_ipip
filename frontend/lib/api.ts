const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3001";

// ---------------------------------------------------------------------------
// Auth token helpers
// ---------------------------------------------------------------------------

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("mindiq_token");
}

export function setAuth(data: AuthResponse) {
  localStorage.setItem("mindiq_token", data.access_token);
  localStorage.setItem("mindiq_session_token", data.session_token); // backwards compat
  localStorage.setItem("mindiq_provider", data.provider);
  if (data.handle) localStorage.setItem("mindiq_handle", data.handle);
}

export function clearAuth() {
  localStorage.removeItem("mindiq_token");
  localStorage.removeItem("mindiq_session_token");
  localStorage.removeItem("mindiq_provider");
  localStorage.removeItem("mindiq_handle");
}

export function isLoggedIn(): boolean {
  return !!getToken();
}

function authHeaders(): Record<string, string> {
  const token = getToken();
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface Question {
  id: string;
  text: string;
  dimension: string;
  reverse: boolean;
  facet?: string;
  scenes?: string[];
  role?: string;
  difficulty?: string;
  tags?: string[];
  language?: string;
}

export interface AssessmentResult {
  id: string;
  completed: boolean;
  paid: boolean;
  scores: Record<string, number> | null;
  percentiles: Record<string, number> | null;
}

export interface PaymentSession {
  checkout_url: string | null;
  mock: boolean;
  assessment_id: string;
}

export interface ReportData {
  assessment_id: string;
  report_html: string;
  scores: Record<string, number>;
  percentiles: Record<string, number>;
}

export interface ProfileBootstrapPayload {
  provider: "x" | "telegram" | "manual";
  handle?: string;
  consent_flags: Record<string, boolean>;
}

export interface ProfileBootstrapResult {
  session_token: string;
  prefill_data: Record<string, unknown>;
  needs_manual_questions: boolean;
}

export interface ProfileSupplementPayload {
  session_token: string;
  answers: Record<string, string>;
  free_text_fields: Record<string, string>;
}

export interface ProfileSupplementResult {
  profile_vector: Record<string, unknown>;
  completeness: number;
}

export interface PersonalizedStartResult {
  assessment_id: string;
  questions: Question[];
  question_ids: string[];
}

export interface OAuthStartResult {
  auth_url: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  provider: string;
  handle: string | null;
  session_token: string;
}

export interface AssessmentSummary {
  id: string;
  created_at: string;
  completed: boolean;
  paid: boolean;
  scores: Record<string, number> | null;
  has_report: boolean;
}

// ---------------------------------------------------------------------------
// Auth endpoints
// ---------------------------------------------------------------------------

export async function emailRegister(payload: {
  email: string;
  password: string;
  name?: string;
}): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || "Registration failed");
  }
  return res.json();
}

export async function emailLogin(payload: {
  email: string;
  password: string;
}): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || "Login failed");
  }
  return res.json();
}

export async function startGoogleOAuth(): Promise<OAuthStartResult> {
  const res = await fetch(`${API_BASE}/api/auth/google/start`);
  if (!res.ok) throw new Error("Failed to start Google OAuth");
  return res.json();
}

export async function finishGoogleOAuth(payload: {
  code: string;
  state: string;
}): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/api/auth/google/callback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to finish Google OAuth");
  return res.json();
}

export async function startWhatsAppOAuth(): Promise<OAuthStartResult> {
  const res = await fetch(`${API_BASE}/api/auth/whatsapp/start`);
  if (!res.ok) throw new Error("Failed to start WhatsApp OAuth");
  return res.json();
}

export async function finishWhatsAppOAuth(payload: {
  code: string;
  state: string;
}): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/api/auth/whatsapp/callback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to finish WhatsApp OAuth");
  return res.json();
}

export async function startTwitterOAuth(): Promise<OAuthStartResult> {
  const res = await fetch(`${API_BASE}/api/auth/twitter/start`);
  if (!res.ok) throw new Error("Failed to start Twitter OAuth");
  return res.json();
}

export async function finishTwitterOAuth(payload: {
  code: string;
  state: string;
}): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/api/auth/twitter/callback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to finish Twitter OAuth");
  return res.json();
}

export async function finishTelegramOAuth(payload: {
  id: string;
  first_name?: string;
  last_name?: string;
  username?: string;
  photo_url?: string;
  auth_date: string;
  hash: string;
}): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/api/auth/telegram/callback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to finish Telegram login");
  return res.json();
}

export async function devLogin(payload: {
  email: string;
  password: string;
}): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/api/auth/dev-login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Dev login failed");
  return res.json();
}

// ---------------------------------------------------------------------------
// Assessment endpoints
// ---------------------------------------------------------------------------

export async function fetchQuestions(): Promise<Question[]> {
  const res = await fetch(`${API_BASE}/api/assessment/questions`);
  if (!res.ok) throw new Error("Failed to fetch questions");
  return res.json();
}

export async function bootstrapProfile(
  payload: ProfileBootstrapPayload
): Promise<ProfileBootstrapResult> {
  const res = await fetch(`${API_BASE}/api/assessment/profile/bootstrap`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to bootstrap profile");
  return res.json();
}

export async function submitProfileSupplement(
  payload: ProfileSupplementPayload
): Promise<ProfileSupplementResult> {
  const res = await fetch(`${API_BASE}/api/assessment/profile/supplement`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to submit profile supplement");
  return res.json();
}

export async function startPersonalizedAssessment(
  sessionToken: string
): Promise<PersonalizedStartResult> {
  const res = await fetch(`${API_BASE}/api/assessment/start-personalized`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ session_token: sessionToken }),
  });
  if (!res.ok) throw new Error("Failed to start personalized assessment");
  return res.json();
}

export async function submitAssessment(
  answers: Record<string, number>
): Promise<AssessmentResult> {
  const res = await fetch(`${API_BASE}/api/assessment/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ answers }),
  });
  if (!res.ok) throw new Error("Failed to submit assessment");
  return res.json();
}

export async function submitAssessmentV2(payload: {
  assessment_id: string;
  session_token?: string;
  answers: Record<string, number>;
}): Promise<AssessmentResult> {
  const res = await fetch(`${API_BASE}/api/assessment/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to submit assessment");
  return res.json();
}

export async function getAssessment(id: string): Promise<AssessmentResult> {
  const res = await fetch(`${API_BASE}/api/assessment/${id}`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error("Assessment not found");
  return res.json();
}

export async function fetchMyAssessments(): Promise<AssessmentSummary[]> {
  const token = getToken();
  const sessionToken = typeof window !== "undefined" ? localStorage.getItem("mindiq_session_token") : null;

  const params = new URLSearchParams();
  if (sessionToken) params.set("session_token", sessionToken);

  const res = await fetch(`${API_BASE}/api/assessment/my-assessments?${params}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) throw new Error("Failed to fetch assessments");
  return res.json();
}

// ---------------------------------------------------------------------------
// Payment endpoints
// ---------------------------------------------------------------------------

export async function createPaymentSession(
  assessmentId: string
): Promise<PaymentSession> {
  const res = await fetch(
    `${API_BASE}/api/payment/create-session/${assessmentId}`,
    { method: "POST", headers: authHeaders() }
  );
  if (!res.ok) throw new Error("Failed to create payment session");
  return res.json();
}

export async function verifyPayment(
  assessmentId: string,
  sessionId?: string,
  mock?: boolean
): Promise<{ paid: boolean; assessment_id: string }> {
  const params = new URLSearchParams({ assessment_id: assessmentId });
  if (sessionId) params.set("session_id", sessionId);
  if (mock) params.set("mock", "true");

  const res = await fetch(`${API_BASE}/api/payment/verify?${params}`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error("Payment verification failed");
  return res.json();
}

// ---------------------------------------------------------------------------
// Report endpoints
// ---------------------------------------------------------------------------

export async function getReport(assessmentId: string): Promise<ReportData> {
  const res = await fetch(`${API_BASE}/api/report/${assessmentId}`, {
    headers: authHeaders(),
  });
  if (!res.ok) {
    if (res.status === 402) throw new Error("Payment required");
    throw new Error("Failed to fetch report");
  }
  return res.json();
}

export function getReportPdfUrl(assessmentId: string): string {
  const token = getToken();
  const base = `${API_BASE}/api/report/${assessmentId}/pdf`;
  return token ? `${base}?token=${encodeURIComponent(token)}` : base;
}

// ---------------------------------------------------------------------------
// Stats
// ---------------------------------------------------------------------------

export async function fetchStats(): Promise<{
  total_assessments: number;
  today_assessments: number;
}> {
  const res = await fetch(`${API_BASE}/api/stats`);
  if (!res.ok) return { total_assessments: 1247, today_assessments: 47 };
  return res.json();
}
