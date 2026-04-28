# CareerDNA India · Phase 3 API/Auth/Payment Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the v3 backend (Phase 1 scoring + Phase 2 content) to a fresh API surface that Phase 4 frontend will consume. Refactor `assessment` / `payment` / `report` routers to use the new `services.scoring` package + `content.*` modules. Add Razorpay mock + production driver, Razorpay webhook handler, Facebook OAuth, short link service, OG image endpoint, and the 5 Phase 3 prep follow-ups deferred from Phase 2 final review.

**Architecture:** Routers become thin adapters: receive request → call into services → return Pydantic-validated response. Heavy lifting (selection, scoring, content composition) stays in the dedicated packages built in Phases 1 + 2. Payment uses a `PaymentDriver` abstraction with `mock` (always-succeed for dev) and `razorpay` (production via `payment_link.create` + webhook signature verification) implementations. Auth gains a Facebook OAuth driver consistent with the existing Google/WhatsApp pattern.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy 2.0, Pydantic v2, `httpx` (already in deps) for Razorpay HTTP, `python-shortuuid` for share codes, `pillow` for OG image generation. No new system deps.

**Spec source:** `docs/superpowers/specs/2026-04-27-careerdna-india-redesign-design.md` (Sections 5 API Surface, S6 Auth/Payment, S7 Sharing)
**Phase 1+2 prerequisite:** commit `54b4cee` (112 backend tests, content layer ready)

---

## Task 1: Phase 2 prep follow-ups

Apply the 5 small fixes deferred at end of Phase 2.

**Files:**
- Modify: `backend/content/cells.py`, `careers.py`, `validators.py`, `models.py`, `milestone_copy.py`
- Modify: `backend/tests/test_content_models.py`

- [ ] **Step 1: Add `__all__` to public content modules**

In `backend/content/cells.py`, add after imports:
```python
__all__ = ["CELLS_DIR", "load_all_cells", "get_cell_content", "clear_cache"]
```

In `backend/content/careers.py`:
```python
__all__ = ["LIBRARY_PATH", "load_career_library", "get_career", "get_careers_for_cell", "clear_cache"]
```

In `backend/content/validators.py`:
```python
__all__ = [
    "find_orphan_career_references",
    "find_unknown_cells_in_why_match",
    "find_cells_with_zero_careers",
    "find_dormant_why_match_entries",
    "validate_content_integrity",
]
```

In `backend/content/models.py`:
```python
__all__ = ["CellId", "CellContent", "CareerEntry", "OceanModifiers", "SalaryRange"]
```

In `backend/services/milestone_copy.py`:
```python
__all__ = ["MILESTONE_THRESHOLDS", "get_milestone_at", "get_copy_for_milestone"]
```

- [ ] **Step 2: Add `clear_cache()` helpers to cells.py and careers.py**

In `cells.py`, append:
```python
def clear_cache() -> None:
    """Clear the cells cache (admin-script use, hot reload after content edits)."""
    _cells_cache.cache_clear()
```

In `careers.py`, append:
```python
def clear_cache() -> None:
    """Clear the career library cache (admin-script use, hot reload after content edits)."""
    _library_cache.cache_clear()
```

- [ ] **Step 3: Add `min_length=1` to `why_match` field**

In `backend/content/models.py`, change:
```python
why_match: dict[CellId, str]
```
to:
```python
why_match: dict[CellId, str] = Field(min_length=1)
```

This catches an empty `why_match` dict at parse time.

- [ ] **Step 4: Add `[link]` substitution helper**

In `backend/content/cells.py`, append:
```python
def render_share_line(line: str, share_url: str) -> str:
    """Substitute [link] token in a share copy line with the actual share URL.

    Designed for backend share-card generation + frontend pre-rendered share text.
    Idempotent: if [link] is absent, returns line unchanged.
    """
    return line.replace("[link]", share_url)
```

Update `__all__` to include `render_share_line`.

- [ ] **Step 5: Add test for `why_match` empty rejection**

In `backend/tests/test_content_models.py`, append:
```python
def test_why_match_rejects_empty_dict():
    """Empty why_match should fail validation (Phase 3 follow-up; prevents broken Path A render)."""
    with pytest.raises(ValidationError):
        CareerEntry(
            career_id="data_scientist",
            name_en="Data Scientist", name_hi="x",
            tagline_en="x" * 30,
            why_match={},  # empty — should fail with min_length=1
            indian_companies=["x", "y"],
            salary_inr=SalaryRange(entry="6L", mid="12L", senior="30L"),
            education_path=["x"], city_distribution=["x"],
        )


def test_render_share_line_substitutes_link():
    from content.cells import render_share_line
    assert render_share_line("Try it → [link]", "https://x.in/abc") == "Try it → https://x.in/abc"
    assert render_share_line("No token here", "https://x.in/abc") == "No token here"  # idempotent
```

- [ ] **Step 6: Run tests + commit**

```bash
source /opt/homebrew/Caskroom/miniconda/base/etc/profile.d/conda.sh && conda activate my_good_ipip && cd /Users/antonio/god/my_good_ipip/backend && pytest tests/ -v
```

Expected: 114 passed (112 prior + 2 new tests).

```bash
cd /Users/antonio/god/my_good_ipip && git add -u backend/ && git commit -m "chore(backend): Phase 3 prep — __all__ exports, clear_cache helpers, why_match min_length, [link] substitution"
```

---

## Task 2: New schemas for v3 API surface

**Files:**
- Modify: `backend/schemas.py` (add v3 request/response models)

- [ ] **Step 1: Add v3 schemas**

Append to `backend/schemas.py`:

```python
# ============================================================================
# Phase 3 v3 schemas (5-demographic + 40-dynamic flow)
# ============================================================================

from pydantic import BaseModel, Field
from typing import Literal


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
    answers: dict[str, int | str]   # str for demographic single_choice values, int for likert_5


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
    riasec_scores: dict[str, int]   # raw 4-20 per type
    holland_radar: dict[str, int]   # alias for riasec_scores, kept distinct for frontend clarity
    careers_preview: list[dict]      # [{career_id, name_en, name_hi, tagline_en, locked: bool}]
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
    careers: list[dict]   # full CareerEntry dump per career_directions
    pdf_path: str | None  # if PDF has been generated


class V3PaymentIntentRequest(BaseModel):
    assessment_id: str


class V3PaymentIntentResponse(BaseModel):
    assessment_id: str
    provider: Literal["mock", "razorpay", "wechat"]
    payment_url: str  # checkout/payment-link URL (or mock success URL)
    amount_inr: int
    promo_active: bool


class V3PaymentWebhookEvent(BaseModel):
    """Razorpay webhook payload (subset)."""
    event: str  # "payment.captured", "payment.failed", etc.
    payload: dict


class V3FacebookCallbackRequest(BaseModel):
    code: str


class V3MilestoneRequest(BaseModel):
    milestone: int  # 10 / 20 / 30 / 40
    seed: str


class V3MilestoneResponse(BaseModel):
    milestone: int
    copy: str


class V3ShareCardOgRequest(BaseModel):
    """For programmatic OG image generation (frontend usually invokes via URL)."""
    assessment_id: str
```

- [ ] **Step 2: Add quick schema test + commit**

In `backend/tests/test_smoke.py` (or new `tests/test_v3_schemas.py`), add:

```python
def test_v3_schemas_importable():
    """Smoke check that all v3 schemas import cleanly."""
    from schemas import (
        DemographicAnswerSubmission,
        V3AssessmentStartRequest,
        V3AssessmentResultResponse,
        V3ReportResponse,
        V3PaymentIntentResponse,
        V3MilestoneResponse,
    )
    # Construct a minimal instance
    DemographicAnswerSubmission(
        DEM_STAGE="experienced", DEM_AGE="25_29", DEM_GENDER="male",
        DEM_CITY_TIER="tier1", DEM_TOP_PRESSURE="career",
    )
```

Run: `pytest tests/test_smoke.py -v` (or `test_v3_schemas.py`); expect new test pass.

Commit:
```bash
git add backend/schemas.py backend/tests/
git commit -m "feat(backend): add v3 API schemas for 45-question + payment + report endpoints"
```

---

## Task 3: PaymentDriver abstraction + mock + Razorpay implementations

**Files:**
- Create: `backend/services/payment/__init__.py`
- Create: `backend/services/payment/base.py`
- Create: `backend/services/payment/mock.py`
- Create: `backend/services/payment/razorpay_driver.py`
- Create: `backend/services/payment/factory.py`
- Create: `backend/tests/test_payment_drivers.py`

Replaces the flat `services.payment_service.py` module's logic; old module kept for legacy callers (similar to scoring pattern).

- [ ] **Step 1: Write failing tests**

`backend/tests/test_payment_drivers.py`:

```python
"""tests/test_payment_drivers.py — payment driver abstraction + implementations."""
import pytest

from services.payment.base import PaymentDriver, PaymentIntent
from services.payment.factory import get_payment_driver
from services.payment.mock import MockDriver


def test_mock_driver_creates_intent():
    driver = MockDriver()
    intent = driver.create_payment_intent("test-assessment-id", amount_inr=49)
    assert isinstance(intent, PaymentIntent)
    assert "mock=true" in intent.payment_url
    assert intent.provider == "mock"
    assert intent.amount_inr == 49


def test_mock_driver_verifies_always_paid():
    driver = MockDriver()
    assert driver.verify_payment("any-txn-id") is True


def test_factory_returns_mock_in_mock_mode(monkeypatch):
    monkeypatch.setenv("PAYMENT_MODE", "mock")
    # Reload config to pick up env change
    import importlib
    import config
    importlib.reload(config)
    driver = get_payment_driver()
    assert isinstance(driver, MockDriver)


def test_razorpay_driver_init_requires_credentials(monkeypatch):
    monkeypatch.setenv("PAYMENT_MODE", "razorpay")
    monkeypatch.setenv("RAZORPAY_KEY_ID", "")
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "")
    import importlib, config
    importlib.reload(config)
    from services.payment.razorpay_driver import RazorpayDriver
    with pytest.raises(ValueError, match="RAZORPAY"):
        RazorpayDriver()


def test_payment_driver_protocol_runtime_check():
    """All drivers conform to the PaymentDriver protocol."""
    driver: PaymentDriver = MockDriver()
    assert hasattr(driver, "create_payment_intent")
    assert hasattr(driver, "verify_payment")
```

Run: expect FAIL (modules don't exist yet).

- [ ] **Step 2: Implement `services/payment/__init__.py` + `base.py`**

`base.py`:

```python
"""Payment driver abstract interface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

PaymentProvider = Literal["mock", "razorpay", "wechat", "stripe"]


@dataclass(frozen=True)
class PaymentIntent:
    """Result of creating a payment intent."""
    provider: PaymentProvider
    assessment_id: str
    payment_url: str
    amount_inr: int
    txn_id: str | None = None
    raw_response: dict | None = None


class PaymentDriver(Protocol):
    """Strategy interface for payment providers.

    Implementations: MockDriver (dev), RazorpayDriver (India production),
    WeChatDriver (internal QA, deferred), StripeDriver (legacy non-India).
    """

    @property
    def provider_name(self) -> PaymentProvider: ...

    def create_payment_intent(self, assessment_id: str, amount_inr: int) -> PaymentIntent: ...

    def verify_payment(self, txn_id: str | None) -> bool: ...

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool: ...
```

`__init__.py`: empty (or `from services.payment.factory import get_payment_driver`).

- [ ] **Step 3: Implement `mock.py`**

```python
"""Mock payment driver — always succeeds. For dev / mock-mode."""

from __future__ import annotations

from config import settings
from services.payment.base import PaymentDriver, PaymentIntent


class MockDriver:
    provider_name = "mock"

    def create_payment_intent(self, assessment_id: str, amount_inr: int) -> PaymentIntent:
        return PaymentIntent(
            provider="mock",
            assessment_id=assessment_id,
            payment_url=f"{settings.FRONTEND_URL}/payment/success?assessment_id={assessment_id}&mock=true",
            amount_inr=amount_inr,
        )

    def verify_payment(self, txn_id: str | None) -> bool:
        return True  # mock mode always considers payment successful

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        return True  # mock mode skips signature checks
```

- [ ] **Step 4: Implement `razorpay_driver.py`**

```python
"""Razorpay payment driver — India production via payment-link API."""

from __future__ import annotations

import hashlib
import hmac
import httpx

from config import settings
from services.payment.base import PaymentDriver, PaymentIntent


_RAZORPAY_BASE = "https://api.razorpay.com/v1"


class RazorpayDriver:
    provider_name = "razorpay"

    def __init__(self) -> None:
        if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
            raise ValueError(
                "RAZORPAY_KEY_ID + RAZORPAY_KEY_SECRET must be set in env "
                "(check env/<env>.env or set PAYMENT_MODE=mock for dev)"
            )

    def _auth(self) -> tuple[str, str]:
        return (settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)

    def create_payment_intent(self, assessment_id: str, amount_inr: int) -> PaymentIntent:
        """Create a Razorpay payment link.

        Razorpay accepts amount in PAISE (INR × 100). UI strings remain in lakh,
        but the API requires paise integers.
        """
        amount_paise = amount_inr * 100
        payload = {
            "amount": amount_paise,
            "currency": "INR",
            "accept_partial": False,
            "description": "CareerDNA Personality Report",
            "notify": {"email": True, "sms": True},
            "reminder_enable": True,
            "callback_url": f"{settings.FRONTEND_URL}/payment/success?assessment_id={assessment_id}",
            "callback_method": "get",
            "notes": {"assessment_id": assessment_id},
        }
        with httpx.Client(timeout=15.0) as client:
            r = client.post(f"{_RAZORPAY_BASE}/payment_links", auth=self._auth(), json=payload)
            r.raise_for_status()
            data = r.json()
        return PaymentIntent(
            provider="razorpay",
            assessment_id=assessment_id,
            payment_url=data["short_url"],
            amount_inr=amount_inr,
            txn_id=data["id"],
            raw_response=data,
        )

    def verify_payment(self, txn_id: str | None) -> bool:
        if not txn_id:
            return False
        with httpx.Client(timeout=15.0) as client:
            r = client.get(f"{_RAZORPAY_BASE}/payment_links/{txn_id}", auth=self._auth())
            if r.status_code != 200:
                return False
            data = r.json()
        return data.get("status") == "paid"

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        if not settings.RAZORPAY_WEBHOOK_SECRET:
            return False
        expected = hmac.new(
            settings.RAZORPAY_WEBHOOK_SECRET.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
```

- [ ] **Step 5: Implement `factory.py`**

```python
"""Payment driver selector keyed off PAYMENT_MODE setting."""

from __future__ import annotations

from config import settings
from services.payment.base import PaymentDriver
from services.payment.mock import MockDriver
from services.payment.razorpay_driver import RazorpayDriver


def get_payment_driver() -> PaymentDriver:
    """Return the configured payment driver.

    Modes:
      - mock      → MockDriver (dev / test)
      - razorpay  → RazorpayDriver (India production)
      - wechat    → WeChatDriver (TBD; not implemented)
      - stripe    → legacy services.payment_service path (kept for non-India)
    """
    mode = settings.PAYMENT_MODE
    if mode == "mock":
        return MockDriver()
    if mode == "razorpay":
        return RazorpayDriver()
    raise ValueError(f"Unsupported PAYMENT_MODE: {mode}")
```

- [ ] **Step 6: Add Razorpay env vars to config**

In `backend/config.py`, add to `Settings`:

```python
RAZORPAY_KEY_ID: str = ""
RAZORPAY_KEY_SECRET: str = ""
RAZORPAY_WEBHOOK_SECRET: str = ""
PROMO_MAX_REDEMPTIONS: int = 1000
PRICE_FULL_INR: int = 99
PRICE_PROMO_INR: int = 49
```

In `env/dev.env`, add (with empty values for dev — mock driver doesn't need them):

```
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
RAZORPAY_WEBHOOK_SECRET=
PROMO_MAX_REDEMPTIONS=1000
PRICE_FULL_INR=99
PRICE_PROMO_INR=49
```

- [ ] **Step 7: Run tests + commit**

```bash
cd /Users/antonio/god/my_good_ipip/backend && pytest tests/test_payment_drivers.py -v
pytest tests/ -v  # full suite
```

Expected: 5 new tests pass; all 119 tests green (114 prior + 5 new).

```bash
git add backend/services/payment/ backend/tests/test_payment_drivers.py backend/config.py env/
git commit -m "feat(backend): add PaymentDriver abstraction + Mock and Razorpay implementations"
```

---

## Task 4: New v3 assessment router

**Files:**
- Create: `backend/routers/assessment_v3.py`
- Modify: `backend/main.py` (mount new router)
- Create: `backend/tests/test_assessment_v3.py`

Mounts new endpoints at `/api/v3/assessment/*` so legacy `/api/assessment/*` keeps working until Phase 4 frontend cuts over.

- [ ] **Step 1: Write failing tests**

`backend/tests/test_assessment_v3.py`:

```python
"""tests/test_assessment_v3.py — v3 assessment endpoints."""
from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_get_demographic_questions():
    r = client.get("/api/v3/assessment/demographic")
    assert r.status_code == 200
    questions = r.json()
    assert len(questions) == 5
    for q in questions:
        assert q["id"].startswith("DEM_")
        assert q["instrument"] == "demographic"
        assert q["response_type"] == "single_choice"
        assert isinstance(q["options"], list)
        assert len(q["options"]) >= 3


def test_start_v3_assessment():
    payload = {
        "demographic": {
            "DEM_STAGE": "experienced",
            "DEM_AGE": "25_29",
            "DEM_GENDER": "male",
            "DEM_CITY_TIER": "tier1",
            "DEM_TOP_PRESSURE": "career",
        }
    }
    r = client.post("/api/v3/assessment/start", json=payload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "assessment_id" in body
    assert "questions" in body
    assert len(body["questions"]) == 40  # 45 minus 5 demographic already answered
    assert "seed" in body


def test_submit_v3_assessment():
    """Full submit flow: start → simulate answers → submit → results."""
    start_payload = {
        "demographic": {
            "DEM_STAGE": "student", "DEM_AGE": "20_24", "DEM_GENDER": "female",
            "DEM_CITY_TIER": "tier1", "DEM_TOP_PRESSURE": "self_doubt",
        }
    }
    start = client.post("/api/v3/assessment/start", json=start_payload).json()
    assessment_id = start["assessment_id"]
    questions = start["questions"]

    answers = {q["id"]: ((i % 5) + 1) for i, q in enumerate(questions)}
    submit_payload = {"assessment_id": assessment_id, "answers": answers}
    r = client.post("/api/v3/assessment/submit", json=submit_payload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["assessment_id"] == assessment_id
    assert "cell_id" in body
    assert len(body["cell_id"]) == 2  # 2-letter Holland cell
    assert "holland_code" in body
    assert len(body["holland_code"]) == 3
    assert "share_code" in body
    assert "careers_preview" in body
    assert len(body["careers_preview"]) >= 3
    # First career fully visible (locked: false), rest locked
    assert body["careers_preview"][0]["locked"] is False
    assert body["is_paid"] is False


def test_get_results_after_submit():
    """GET /results returns the same shape as POST /submit response (idempotent)."""
    start_payload = {
        "demographic": {
            "DEM_STAGE": "founder", "DEM_AGE": "30_34", "DEM_GENDER": "male",
            "DEM_CITY_TIER": "tier1", "DEM_TOP_PRESSURE": "career",
        }
    }
    start = client.post("/api/v3/assessment/start", json=start_payload).json()
    assessment_id = start["assessment_id"]
    answers = {q["id"]: ((i % 5) + 1) for i, q in enumerate(start["questions"])}
    client.post("/api/v3/assessment/submit", json={"assessment_id": assessment_id, "answers": answers})

    r = client.get(f"/api/v3/assessment/{assessment_id}/results")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["assessment_id"] == assessment_id
    assert body["is_paid"] is False


def test_milestone_copy_endpoint():
    r = client.get("/api/v3/assessment/milestone?milestone=20&seed=test-seed")
    assert r.status_code == 200
    body = r.json()
    assert body["milestone"] == 20
    assert isinstance(body["copy"], str) and len(body["copy"]) >= 10


def test_milestone_copy_invalid_milestone_400():
    r = client.get("/api/v3/assessment/milestone?milestone=15&seed=x")
    assert r.status_code == 400
```

Run: expect FAIL (router doesn't exist).

- [ ] **Step 2: Implement `backend/routers/assessment_v3.py`**

```python
"""v3 Assessment router — 5-demographic + 40-dynamic flow + scoring + content composition."""

from __future__ import annotations

from secrets import token_urlsafe

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from content.careers import get_career, get_careers_for_cell
from content.cells import get_cell_content, render_share_line
from database import get_db
from models import Assessment, ShortLink
from questions.demographic import DEMOGRAPHIC_QUESTIONS
from questions.selector import select_45_questions
from schemas import (
    V3AnswerSubmission,
    V3AssessmentResultResponse,
    V3AssessmentStartRequest,
    V3AssessmentStartResponse,
    V3MilestoneResponse,
    V3QuestionOut,
)
from services.milestone_copy import MILESTONE_THRESHOLDS, get_copy_for_milestone
from services.scoring.archetype import check_mast_trigger, derive_archetype_cell
from services.scoring.holland_code import compute_holland_code
from services.scoring.ocean import compute_ocean_percentiles, compute_ocean_scores
from services.scoring.riasec import compute_riasec_scores

from config import settings


router = APIRouter(prefix="/api/v3/assessment", tags=["assessment_v3"])


def _question_to_payload(q) -> V3QuestionOut:
    """Convert internal Question dataclass to public V3QuestionOut."""
    return V3QuestionOut(
        id=q.id,
        text=q.text_en,
        instrument=q.instrument.value if hasattr(q.instrument, "value") else q.instrument,
        response_type=q.response_type.value if hasattr(q.response_type, "value") else q.response_type,
        options=q.options,
    )


@router.get("/demographic", response_model=list[V3QuestionOut])
def get_demographic_questions():
    """Return Q1-Q5 demographic questions. Frontend renders these first; user answers
    feed `/start` to receive the remaining 40 personalized questions."""
    return [_question_to_payload(q) for q in DEMOGRAPHIC_QUESTIONS]


@router.post("/start", response_model=V3AssessmentStartResponse)
def start_assessment(payload: V3AssessmentStartRequest, db: Session = Depends(get_db)):
    """Receive demographic answers, return next 40 questions + create Assessment record."""
    seed = token_urlsafe(16)
    demographic_answers = payload.demographic.model_dump()
    selected = select_45_questions(demographic_answers, seed=seed)
    # Drop demographic from returned list (frontend already has those answers)
    next_40 = [q for q in selected if not q.id.startswith("DEM_")]

    assessment = Assessment(
        completed=False,
        paid=False,
        demographic=demographic_answers,
        question_set_version="v3_45_hybrid",
        question_ids=[q.id for q in selected],
        selection_seed=seed,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    return V3AssessmentStartResponse(
        assessment_id=assessment.id,
        questions=[_question_to_payload(q) for q in next_40],
        seed=seed,
    )


@router.post("/submit", response_model=V3AssessmentResultResponse)
def submit_assessment(payload: V3AnswerSubmission, db: Session = Depends(get_db)):
    """Submit all 45 answers (5 demographic from /start + 40 from this submit), score, and compose results."""
    assessment = db.query(Assessment).filter(Assessment.id == payload.assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if assessment.completed:
        raise HTTPException(status_code=400, detail="Already submitted; use GET /results")

    # Merge demographic answers (already on the assessment) with submitted answers
    full_answers: dict = {}
    full_answers.update(assessment.demographic or {})
    full_answers.update(payload.answers)

    # Validate that all expected question_ids are answered
    expected_ids = set(assessment.question_ids or [])
    received_ids = set(full_answers.keys())
    missing = expected_ids - received_ids
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing answers for {len(missing)} questions: {sorted(missing)[:5]}...",
        )

    # Score
    riasec = compute_riasec_scores({k: v for k, v in payload.answers.items() if isinstance(v, int)})
    ocean = compute_ocean_scores({k: v for k, v in payload.answers.items() if isinstance(v, int)})
    ocean_pct = compute_ocean_percentiles(ocean)
    holland_code = compute_holland_code(riasec)
    cell_id = derive_archetype_cell(riasec, holland_code)
    mast = check_mast_trigger(ocean_pct, riasec)

    # Persist
    assessment.answers = payload.answers
    assessment.completed = True
    assessment.riasec_scores = riasec
    assessment.ocean_scores = ocean
    assessment.ocean_percentiles = ocean_pct
    assessment.holland_code = holland_code
    assessment.archetype_cell = cell_id

    # Generate share code + persist short link
    share_code = token_urlsafe(6)[:8]
    assessment.share_code = share_code
    canonical_url = f"{settings.FRONTEND_URL}/results/{assessment.id}"
    db.add(ShortLink(code=share_code, assessment_id=assessment.id, target_url=canonical_url))
    db.commit()
    db.refresh(assessment)

    return _compose_results_response(assessment, db)


@router.get("/{assessment_id}/results", response_model=V3AssessmentResultResponse)
def get_results(assessment_id: str, db: Session = Depends(get_db)):
    """GET endpoint for re-fetching results after submit. Free 5-screen data only."""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if not assessment.completed:
        raise HTTPException(status_code=400, detail="Assessment not yet submitted")
    return _compose_results_response(assessment, db)


def _compose_results_response(assessment: Assessment, db: Session) -> V3AssessmentResultResponse:
    """Build the V3AssessmentResultResponse from a completed Assessment."""
    cell_id = assessment.archetype_cell
    cell_content = get_cell_content(cell_id)

    # Free preview: career #1 fully shown, rest locked
    careers_full = get_careers_for_cell(cell_id)
    careers_preview = []
    for i, career in enumerate(careers_full):
        careers_preview.append({
            "career_id": career.career_id,
            "name_en": career.name_en,
            "name_hi": career.name_hi,
            "tagline_en": career.tagline_en if i == 0 else None,
            "salary_inr_summary": (
                f"₹{career.salary_inr.entry}–{career.salary_inr.senior}"
                if i == 0 else None
            ),
            "locked": i > 0,
        })

    share_url = f"{settings.FRONTEND_URL}/s/{assessment.share_code}" if assessment.share_code else ""

    return V3AssessmentResultResponse(
        assessment_id=assessment.id,
        cell_id=cell_id,
        cell_label_en=cell_content.label_en,
        cell_label_hi=cell_content.label_hi,
        slogan_en=cell_content.slogan_en,
        rarity_pct=cell_content.rarity_pct,
        core_insight_en=cell_content.core_insight_en,
        holland_code=assessment.holland_code,
        riasec_scores=assessment.riasec_scores,
        holland_radar=assessment.riasec_scores,  # frontend alias for clarity
        careers_preview=careers_preview,
        share_code=assessment.share_code or "",
        share_url=share_url,
        is_paid=assessment.paid,
        is_mast_trigger=False,  # MAST triggers stored separately if needed
    )


@router.get("/milestone", response_model=V3MilestoneResponse)
def get_milestone_copy_endpoint(
    milestone: int = Query(..., description="Q10 / Q20 / Q30 / Q40"),
    seed: str = Query(..., description="Per-user seed (assessment_id or seed token)"),
):
    if milestone not in MILESTONE_THRESHOLDS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid milestone {milestone!r}; must be one of {MILESTONE_THRESHOLDS}",
        )
    return V3MilestoneResponse(milestone=milestone, copy=get_copy_for_milestone(milestone, seed))
```

- [ ] **Step 3: Mount router in `backend/main.py`**

```python
from routers import assessment, assessment_v3, auth, payment, report

app.include_router(assessment.router)
app.include_router(assessment_v3.router)  # NEW v3
app.include_router(auth.router)
app.include_router(payment.router)
app.include_router(report.router)
```

- [ ] **Step 4: Run tests + commit**

```bash
cd /Users/antonio/god/my_good_ipip/backend && pytest tests/test_assessment_v3.py -v
pytest tests/ -v
```

Expected: 6 new tests pass; full suite green (125 total: 119 prior + 6 new).

```bash
git add backend/routers/assessment_v3.py backend/main.py backend/tests/test_assessment_v3.py
git commit -m "feat(backend): add v3 assessment router with 5+40 demographic-dynamic flow + content composition"
```

---

## Task 5: New v3 payment router with Razorpay + webhook

**Files:**
- Create: `backend/routers/payment_v3.py`
- Modify: `backend/main.py` (mount)
- Create: `backend/tests/test_payment_v3.py`

- [ ] **Step 1: Failing tests**

```python
"""tests/test_payment_v3.py"""
from fastapi.testclient import TestClient

from main import app
from models import Assessment
from database import SessionLocal


client = TestClient(app)


def _create_completed_assessment(db) -> Assessment:
    """Helper: create an assessment in the DB for payment tests."""
    a = Assessment(completed=True, paid=False, archetype_cell="IA")
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


def test_create_payment_intent_mock_mode(monkeypatch):
    monkeypatch.setenv("PAYMENT_MODE", "mock")
    db = SessionLocal()
    a = _create_completed_assessment(db)
    db.close()

    r = client.post("/api/v3/payment/create-intent", json={"assessment_id": a.id})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["provider"] == "mock"
    assert "mock=true" in body["payment_url"]
    assert body["amount_inr"] in (49, 99)


def test_create_payment_intent_unknown_assessment_404():
    r = client.post("/api/v3/payment/create-intent", json={"assessment_id": "nonexistent"})
    assert r.status_code == 404


def test_create_payment_intent_incomplete_assessment_400():
    db = SessionLocal()
    a = Assessment(completed=False, paid=False)
    db.add(a)
    db.commit()
    db.refresh(a)
    db.close()
    r = client.post("/api/v3/payment/create-intent", json={"assessment_id": a.id})
    assert r.status_code == 400


def test_promo_pricing_active_for_first_users(monkeypatch):
    """If paid_count < PROMO_MAX_REDEMPTIONS, price is PROMO."""
    monkeypatch.setenv("PAYMENT_MODE", "mock")
    monkeypatch.setenv("PROMO_MAX_REDEMPTIONS", "1000")
    db = SessionLocal()
    a = _create_completed_assessment(db)
    db.close()
    r = client.post("/api/v3/payment/create-intent", json={"assessment_id": a.id})
    body = r.json()
    assert body["promo_active"] is True


def test_webhook_endpoint_exists():
    """Webhook accepts POST; signature failure returns 401."""
    r = client.post("/api/v3/payment/webhook/razorpay", json={"event": "payment.captured", "payload": {}})
    # In mock mode this might bypass; in razorpay mode missing signature → 401.
    # Just verify endpoint is registered (200 or 401, not 404).
    assert r.status_code != 404
```

- [ ] **Step 2: Implement `routers/payment_v3.py`**

```python
"""v3 Payment router — Razorpay-aware with mock fallback + webhook handler."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models import Assessment
from schemas import V3PaymentIntentRequest, V3PaymentIntentResponse
from services.payment.factory import get_payment_driver


router = APIRouter(prefix="/api/v3/payment", tags=["payment_v3"])


def _current_price(db: Session) -> tuple[int, bool]:
    """Return (amount_inr, promo_active) based on paid count vs cap."""
    paid_count = db.query(Assessment).filter(Assessment.payment_status == "confirmed").count()
    if paid_count < settings.PROMO_MAX_REDEMPTIONS:
        return settings.PRICE_PROMO_INR, True
    return settings.PRICE_FULL_INR, False


@router.post("/create-intent", response_model=V3PaymentIntentResponse)
def create_intent(payload: V3PaymentIntentRequest, db: Session = Depends(get_db)):
    assessment = db.query(Assessment).filter(Assessment.id == payload.assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if not assessment.completed:
        raise HTTPException(status_code=400, detail="Assessment not yet completed")
    if assessment.paid:
        raise HTTPException(status_code=400, detail="Already paid")

    amount_inr, promo_active = _current_price(db)
    driver = get_payment_driver()
    intent = driver.create_payment_intent(assessment.id, amount_inr=amount_inr)

    assessment.payment_provider = intent.provider
    assessment.payment_txn_id = intent.txn_id
    assessment.payment_amount_inr = amount_inr
    assessment.payment_status = "pending"
    db.commit()

    return V3PaymentIntentResponse(
        assessment_id=assessment.id,
        provider=intent.provider,
        payment_url=intent.payment_url,
        amount_inr=amount_inr,
        promo_active=promo_active,
    )


@router.post("/webhook/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """Razorpay webhook handler — verifies signature, marks assessment paid on payment.captured."""
    raw_body = await request.body()
    driver = get_payment_driver()
    if not driver.verify_webhook_signature(raw_body, x_razorpay_signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    import json
    event = json.loads(raw_body)
    if event.get("event") == "payment_link.paid":
        link_id = event["payload"]["payment_link"]["entity"]["id"]
        assessment = db.query(Assessment).filter(Assessment.payment_txn_id == link_id).first()
        if assessment and assessment.payment_status != "confirmed":
            assessment.paid = True
            assessment.payment_status = "confirmed"
            db.commit()

    return {"received": True}


@router.get("/verify/{assessment_id}")
def verify_payment(assessment_id: str, db: Session = Depends(get_db)):
    """Polling endpoint for clients to check payment status."""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    # If pending and we have a txn_id, poll the driver
    if assessment.payment_status == "pending" and assessment.payment_txn_id:
        driver = get_payment_driver()
        if driver.verify_payment(assessment.payment_txn_id):
            assessment.paid = True
            assessment.payment_status = "confirmed"
            db.commit()

    return {"assessment_id": assessment_id, "paid": assessment.paid, "status": assessment.payment_status}
```

- [ ] **Step 3: Mount router + run tests + commit**

In `main.py`: `from routers import assessment_v3, payment_v3` and `app.include_router(payment_v3.router)`.

```bash
cd /Users/antonio/god/my_good_ipip/backend && pytest tests/test_payment_v3.py -v
pytest tests/ -v
```

Expected: 5 new tests pass; 130 total green.

```bash
git add backend/routers/payment_v3.py backend/main.py backend/tests/test_payment_v3.py
git commit -m "feat(backend): add v3 payment router with Razorpay intent + webhook + promo pricing"
```

---

## Task 6: New v3 report router (paid-only deep report)

**Files:**
- Create: `backend/routers/report_v3.py`
- Modify: `backend/main.py`
- Create: `backend/tests/test_report_v3.py`

- [ ] **Step 1: Failing tests**

```python
"""tests/test_report_v3.py"""
from fastapi.testclient import TestClient

from main import app
from database import SessionLocal
from models import Assessment


client = TestClient(app)


def test_report_unpaid_402():
    db = SessionLocal()
    a = Assessment(completed=True, paid=False, archetype_cell="IA",
                    riasec_scores={"R":10,"I":18,"A":15,"S":8,"E":11,"C":13},
                    ocean_scores={"openness":80,"conscientiousness":70,"extraversion":50,"agreeableness":60,"neuroticism":40},
                    ocean_percentiles={"openness":92,"conscientiousness":75,"extraversion":50,"agreeableness":62,"neuroticism":35},
                    holland_code="IAC")
    db.add(a); db.commit(); db.refresh(a)
    r = client.get(f"/api/v3/report/{a.id}")
    assert r.status_code == 402


def test_report_paid_returns_full():
    db = SessionLocal()
    a = Assessment(completed=True, paid=True, archetype_cell="IA",
                    riasec_scores={"R":10,"I":18,"A":15,"S":8,"E":11,"C":13},
                    ocean_scores={"openness":80,"conscientiousness":70,"extraversion":50,"agreeableness":60,"neuroticism":40},
                    ocean_percentiles={"openness":92,"conscientiousness":75,"extraversion":50,"agreeableness":62,"neuroticism":35},
                    holland_code="IAC")
    db.add(a); db.commit(); db.refresh(a)
    r = client.get(f"/api/v3/report/{a.id}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["cell_id"] == "IA"
    assert "deep_description_en" in body
    assert len(body["strengths_en"]) == 5
    assert len(body["growth_tips_en"]) == 5
    assert len(body["careers"]) >= 3
```

- [ ] **Step 2: Implement `routers/report_v3.py`**

```python
"""v3 Report router — paid-only full report composing cell + careers + OCEAN."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from content.careers import get_careers_for_cell
from content.cells import get_cell_content
from database import get_db
from models import Assessment
from schemas import V3ReportResponse


router = APIRouter(prefix="/api/v3/report", tags=["report_v3"])


def _require_paid(assessment: Assessment) -> None:
    if not assessment.paid:
        raise HTTPException(status_code=402, detail="Payment required")


@router.get("/{assessment_id}", response_model=V3ReportResponse)
def get_report(assessment_id: str, db: Session = Depends(get_db)):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if not assessment.completed:
        raise HTTPException(status_code=400, detail="Assessment not yet completed")
    _require_paid(assessment)

    cell = get_cell_content(assessment.archetype_cell)
    careers_full = get_careers_for_cell(assessment.archetype_cell)
    careers_dump = [
        {
            "career_id": c.career_id,
            "name_en": c.name_en,
            "name_hi": c.name_hi,
            "tagline_en": c.tagline_en,
            "why_match": c.why_match,
            "indian_companies": c.indian_companies,
            "salary_inr": {"entry": c.salary_inr.entry, "mid": c.salary_inr.mid, "senior": c.salary_inr.senior},
            "education_path": c.education_path,
            "city_distribution": c.city_distribution,
        }
        for c in careers_full
    ]

    return V3ReportResponse(
        assessment_id=assessment.id,
        cell_id=assessment.archetype_cell,
        cell_label_en=cell.label_en,
        cell_label_hi=cell.label_hi,
        slogan_en=cell.slogan_en,
        deep_description_en=cell.deep_description_en,
        strengths_en=cell.strengths_en,
        growth_tips_en=cell.growth_tips_en,
        ocean_scores=assessment.ocean_scores,
        ocean_percentiles=assessment.ocean_percentiles,
        holland_code=assessment.holland_code,
        riasec_scores=assessment.riasec_scores,
        rarity_pct=cell.rarity_pct,
        is_mast_trigger=False,
        careers=careers_dump,
        pdf_path=assessment.pdf_path,
    )
```

- [ ] **Step 3: Mount + tests + commit**

In `main.py`: `from routers import assessment_v3, payment_v3, report_v3` and `app.include_router(report_v3.router)`.

```bash
pytest tests/test_report_v3.py -v && pytest tests/ -v
```

Expected: 132 tests pass.

```bash
git add backend/routers/report_v3.py backend/main.py backend/tests/test_report_v3.py
git commit -m "feat(backend): add v3 report router with paid-only deep report (cell + OCEAN + careers)"
```

---

## Task 7: Facebook OAuth + share infrastructure

**Files:**
- Modify: `backend/services/oauth_service.py` (add Facebook helpers)
- Modify: `backend/routers/auth.py` (add Facebook endpoints)
- Create: `backend/routers/share.py` (short link + OG image stub)
- Create: `backend/tests/test_share.py`

- [ ] **Step 1: Add Facebook OAuth helpers**

In `backend/services/oauth_service.py`, add functions following the Google pattern:

```python
def build_facebook_authorize_url() -> str:
    if not settings.FACEBOOK_APP_ID:
        raise ValueError("FACEBOOK_APP_ID not configured")
    redirect_uri = f"{settings.FRONTEND_URL}/auth/facebook/callback"
    return (
        "https://www.facebook.com/v18.0/dialog/oauth"
        f"?client_id={settings.FACEBOOK_APP_ID}"
        f"&redirect_uri={redirect_uri}"
        "&scope=email,public_profile"
        "&response_type=code"
    )


async def exchange_facebook_code(code: str) -> dict:
    if not settings.FACEBOOK_APP_ID or not settings.FACEBOOK_APP_SECRET:
        raise ValueError("Facebook OAuth not configured")
    redirect_uri = f"{settings.FRONTEND_URL}/auth/facebook/callback"
    async with httpx.AsyncClient(timeout=15.0) as client:
        token_resp = await client.get(
            "https://graph.facebook.com/v18.0/oauth/access_token",
            params={
                "client_id": settings.FACEBOOK_APP_ID,
                "client_secret": settings.FACEBOOK_APP_SECRET,
                "redirect_uri": redirect_uri,
                "code": code,
            },
        )
        token_resp.raise_for_status()
        token = token_resp.json()["access_token"]

        me_resp = await client.get(
            "https://graph.facebook.com/me",
            params={"fields": "id,name,email", "access_token": token},
        )
        me_resp.raise_for_status()
        me = me_resp.json()

    return {
        "external_id": me["id"],
        "handle": me.get("name"),
        "email": me.get("email"),
        "public": {"name": me.get("name")},
    }
```

Add `FACEBOOK_APP_ID` / `FACEBOOK_APP_SECRET` to `config.Settings`.

- [ ] **Step 2: Add Facebook router endpoints**

In `backend/routers/auth.py`, add:

```python
from services.oauth_service import (
    ...,
    build_facebook_authorize_url,
    exchange_facebook_code,
)


@router.get("/facebook/start", response_model=OAuthStartResponse)
def facebook_start():
    try:
        return OAuthStartResponse(auth_url=build_facebook_authorize_url())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/facebook/callback", response_model=AuthResponse)
async def facebook_callback(payload: OAuthFinishRequest, db: Session = Depends(get_db)):
    try:
        identity = await exchange_facebook_code(payload.code)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Facebook OAuth failed: {exc}") from exc
    profile = _upsert_profile(
        provider="facebook",
        external_id=identity["external_id"],
        handle=identity.get("handle"),
        public_data=identity.get("public", {}),
        db=db,
        email=identity.get("email"),
    )
    return _auth_response(profile, "facebook")
```

- [ ] **Step 3: Create `backend/routers/share.py`**

```python
"""Share router — short-link redirect + OG image proxy."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.orm import Session

from database import get_db
from models import Assessment, ShortLink

router = APIRouter(tags=["share"])


@router.get("/s/{code}")
def short_link_redirect(code: str, db: Session = Depends(get_db)):
    link = db.query(ShortLink).filter(ShortLink.code == code).first()
    if not link:
        raise HTTPException(status_code=404, detail="Short link not found")
    link.clicks += 1
    db.commit()
    return RedirectResponse(url=link.target_url, status_code=302)


@router.get("/api/share/{assessment_id}/og.png")
def og_image_stub(assessment_id: str, db: Session = Depends(get_db)):
    """OG image generation stub. Phase 4 frontend uses Next.js @vercel/og to render
    rich PNGs at the edge. This backend stub returns a minimal 1×1 PNG so backend
    smoke tests pass; production frontend should NOT call this endpoint."""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    # 1×1 transparent PNG
    return Response(
        content=bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489000000d49444154789c63000100000005000156a51b29000000004945e426"),
        media_type="image/png",
    )
```

- [ ] **Step 4: Tests + commit**

`backend/tests/test_share.py`:

```python
from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
from models import Assessment, ShortLink


client = TestClient(app)


def test_short_link_redirects():
    db = SessionLocal()
    a = Assessment(completed=True)
    db.add(a); db.commit(); db.refresh(a)
    link = ShortLink(code="abc12345", assessment_id=a.id, target_url="https://careerdna.in/results/abc")
    db.add(link); db.commit()
    db.close()

    r = client.get("/s/abc12345", follow_redirects=False)
    assert r.status_code == 302
    assert "https://careerdna.in" in r.headers.get("location", "")


def test_og_stub_returns_png():
    db = SessionLocal()
    a = Assessment(completed=True)
    db.add(a); db.commit(); db.refresh(a)
    db.close()
    r = client.get(f"/api/share/{a.id}/og.png")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
```

Mount in `main.py`: `from routers import share` and `app.include_router(share.router)`.

```bash
pytest tests/test_share.py -v && pytest tests/ -v
```

```bash
git add backend/services/oauth_service.py backend/routers/auth.py backend/routers/share.py backend/main.py backend/config.py backend/tests/test_share.py
git commit -m "feat(backend): add Facebook OAuth + short link redirect + OG image stub"
```

---

## Task 8: E2E v3 backend test

**Files:**
- Create: `backend/tests/test_v3_e2e.py`

- [ ] **Step 1: Write E2E test covering the full v1 user journey**

```python
"""tests/test_v3_e2e.py — full v3 backend user journey."""
from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_full_v3_journey_mock_payment(monkeypatch):
    """End-to-end: demographic → start → submit → pay → fetch report."""
    monkeypatch.setenv("PAYMENT_MODE", "mock")

    # 1. Get demographic Q1-5
    r = client.get("/api/v3/assessment/demographic")
    assert r.status_code == 200 and len(r.json()) == 5

    # 2. Start assessment with demographic answers
    start_payload = {
        "demographic": {
            "DEM_STAGE": "experienced", "DEM_AGE": "25_29", "DEM_GENDER": "male",
            "DEM_CITY_TIER": "tier1", "DEM_TOP_PRESSURE": "career",
        }
    }
    start = client.post("/api/v3/assessment/start", json=start_payload).json()
    assessment_id = start["assessment_id"]

    # 3. Get milestone copy at Q20
    milestone = client.get(f"/api/v3/assessment/milestone?milestone=20&seed={start['seed']}").json()
    assert milestone["milestone"] == 20

    # 4. Submit answers
    answers = {q["id"]: ((i % 5) + 1) for i, q in enumerate(start["questions"])}
    result = client.post("/api/v3/assessment/submit", json={"assessment_id": assessment_id, "answers": answers}).json()
    assert result["is_paid"] is False
    assert "share_code" in result

    # 5. Try to fetch report — should 402 (unpaid)
    r = client.get(f"/api/v3/report/{assessment_id}")
    assert r.status_code == 402

    # 6. Create payment intent
    intent = client.post("/api/v3/payment/create-intent", json={"assessment_id": assessment_id}).json()
    assert intent["provider"] == "mock"

    # 7. Mark paid via verify endpoint (mock driver returns paid=True)
    verify = client.get(f"/api/v3/payment/verify/{assessment_id}").json()
    assert verify["paid"] is True

    # 8. Now fetch report
    report = client.get(f"/api/v3/report/{assessment_id}").json()
    assert report["cell_id"] == result["cell_id"]
    assert len(report["strengths_en"]) == 5
    assert len(report["careers"]) >= 3

    # 9. Resolve share code
    short = client.get(f"/s/{result['share_code']}", follow_redirects=False)
    assert short.status_code == 302
```

- [ ] **Step 2: Run + commit**

```bash
cd /Users/antonio/god/my_good_ipip/backend && pytest tests/test_v3_e2e.py -v
pytest tests/ -v
```

Expected: 1 new E2E test + ~140 total backend tests passing.

```bash
git add backend/tests/test_v3_e2e.py
git commit -m "feat(backend): add v3 backend E2E test (demographic → submit → pay → report → share)"
```

---

## Phase 3 Acceptance Criteria

- [ ] `pytest tests/ -v` returns ≥ 140 passing tests, 0 failures
- [ ] All v3 endpoints respond 200 on happy path:
  - `GET /api/v3/assessment/demographic`
  - `POST /api/v3/assessment/start`
  - `POST /api/v3/assessment/submit`
  - `GET /api/v3/assessment/{id}/results`
  - `GET /api/v3/assessment/milestone`
  - `POST /api/v3/payment/create-intent`
  - `POST /api/v3/payment/webhook/razorpay`
  - `GET /api/v3/payment/verify/{id}`
  - `GET /api/v3/report/{id}` (402 when unpaid, 200 when paid)
  - `GET /s/{code}` (302 redirect)
  - `GET /api/share/{id}/og.png` (PNG)
- [ ] Razorpay driver implementation works in mock mode (production untested without real keys)
- [ ] Facebook OAuth start + callback endpoints registered
- [ ] Phase 1+2 tests still pass (no regressions)
- [ ] Conventional commit messages

---

## Phase 3 → Spec Coverage

- ✅ S6 §3.15 Auth Flow — Task 7 (Facebook added; existing providers preserved)
- ✅ S6 §3.16 Payment Driver — Tasks 3 + 5 (Razorpay + mock; WeChat/Stripe deferred)
- ✅ S7 §3.17–3.20 Sharing — Task 7 (short link + OG stub)
- ✅ §5 API Surface — Tasks 4, 5, 6, 7
- ✅ Phase 2 prep follow-ups — Task 1
- ⏭ S8 §3.21–3.23 UI — Phase 4
- ⏭ §3.6 Milestone UI rendering — Phase 4

---

## Estimated Effort

~12-16 hours engineering. Most complex tasks: Razorpay driver (~3h), v3 assessment router (~3h), E2E test (~2h). Other tasks ~1-2h each.

---

## Phase 3 — IN PROGRESS

Plan saved. Execution proceeds via subagent-driven development.
