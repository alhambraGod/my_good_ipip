from typing import Any, Literal

from pydantic import BaseModel, Field


class AnswerSubmission(BaseModel):
    answers: dict[str, int]  # {question_id: likert_value (1-5)}
    assessment_id: str | None = None
    session_token: str | None = None


class AssessmentResponse(BaseModel):
    id: str
    completed: bool
    paid: bool
    scores: dict[str, float] | None = None
    percentiles: dict[str, int] | None = None


class PaymentCreateResponse(BaseModel):
    checkout_url: str | None = None
    mock: bool = False
    assessment_id: str = ""


class PaymentVerifyResponse(BaseModel):
    paid: bool
    assessment_id: str


class ReportResponse(BaseModel):
    assessment_id: str
    report_html: str
    scores: dict[str, float]
    percentiles: dict[str, int]


class QuestionOut(BaseModel):
    id: str
    text: str
    dimension: str
    reverse: bool
    facet: str | None = None
    scenes: list[str] = Field(default_factory=list)
    role: str | None = None
    difficulty: str | None = None
    tags: list[str] = Field(default_factory=list)
    language: str | None = None


class ProfileBootstrapRequest(BaseModel):
    provider: Literal["x", "telegram", "manual"]
    handle: str | None = None
    consent_flags: dict[str, bool] = Field(default_factory=dict)


class ProfileBootstrapResponse(BaseModel):
    session_token: str
    prefill_data: dict[str, Any] = Field(default_factory=dict)
    needs_manual_questions: bool


class ProfileSupplementRequest(BaseModel):
    session_token: str
    answers: dict[str, str] = Field(default_factory=dict)
    free_text_fields: dict[str, str] = Field(default_factory=dict)


class ProfileSupplementResponse(BaseModel):
    profile_vector: dict[str, Any]
    completeness: float


class PersonalizedQuestionStartRequest(BaseModel):
    session_token: str


class PersonalizedQuestionStartResponse(BaseModel):
    assessment_id: str
    questions: list[QuestionOut]
    question_ids: list[str]


class OAuthStartResponse(BaseModel):
    auth_url: str


class OAuthFinishRequest(BaseModel):
    code: str
    state: str


class OAuthSessionResponse(BaseModel):
    session_token: str
    provider: Literal["x", "telegram", "manual", "email", "google", "whatsapp"]
    handle: str | None = None


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    provider: Literal["x", "telegram", "manual", "email", "google", "whatsapp"]
    handle: str | None = None
    session_token: str  # backwards compat


class DevLoginRequest(BaseModel):
    email: str
    password: str


class TelegramCallbackRequest(BaseModel):
    id: str
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    photo_url: str | None = None
    auth_date: str
    hash: str


class AssessmentSummary(BaseModel):
    id: str
    created_at: str
    completed: bool
    paid: bool
    scores: dict[str, float] | None = None
    has_report: bool


class EmailRegisterRequest(BaseModel):
    email: str
    password: str
    name: str | None = None


class EmailLoginRequest(BaseModel):
    email: str
    password: str


# ============================================================================
# Phase 3 v3 schemas (5-demographic + 40-dynamic flow)
# ============================================================================


class DemographicAnswerSubmission(BaseModel):
    """5 demographic answers from Q1-5."""
    DEM_STAGE: str
    DEM_AGE: str
    DEM_GENDER: str
    DEM_CITY_TIER: str
    DEM_TOP_PRESSURE: str


class V3AssessmentStartRequest(BaseModel):
    demographic: DemographicAnswerSubmission


class V3QuestionOut(BaseModel):
    """Public-facing question shape (no scoring metadata)."""
    id: str
    text: str
    instrument: Literal["riasec", "ipip", "demographic", "interest"]
    response_type: Literal["likert_5", "single_choice", "multi_choice"]
    options: list[dict] | None = None


class V3AssessmentStartResponse(BaseModel):
    assessment_id: str
    questions: list[V3QuestionOut]
    seed: str


class V3AnswerSubmission(BaseModel):
    assessment_id: str
    answers: dict[str, int | str]


class V3AssessmentResultResponse(BaseModel):
    """Free 5-screen result data (no OCEAN, partial career details)."""
    assessment_id: str
    cell_id: str
    cell_label_en: str
    cell_label_hi: str
    slogan_en: str
    rarity_pct: float
    core_insight_en: str
    holland_code: str
    riasec_scores: dict[str, int]
    holland_radar: dict[str, int]
    careers_preview: list[dict]
    share_code: str
    share_url: str
    is_paid: bool
    is_mast_trigger: bool


class V3ReportResponse(BaseModel):
    """Full paid report (Phase 4 result page Screen 5+ unlocks this)."""
    assessment_id: str
    cell_id: str
    cell_label_en: str
    cell_label_hi: str
    slogan_en: str
    deep_description_en: str
    strengths_en: list[str]
    growth_tips_en: list[str]
    ocean_scores: dict[str, float]
    ocean_percentiles: dict[str, int]
    holland_code: str
    riasec_scores: dict[str, int]
    rarity_pct: float
    is_mast_trigger: bool
    careers: list[dict]
    pdf_path: str | None


class V3PaymentIntentRequest(BaseModel):
    assessment_id: str


class V3PaymentIntentResponse(BaseModel):
    assessment_id: str
    provider: Literal["mock", "razorpay", "wechat", "stripe"]
    payment_url: str
    amount_inr: int
    promo_active: bool


class V3FacebookCallbackRequest(BaseModel):
    code: str


class V3MilestoneRequest(BaseModel):
    milestone: int
    seed: str


class V3MilestoneResponse(BaseModel):
    milestone: int
    copy: str
