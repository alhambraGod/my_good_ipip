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
