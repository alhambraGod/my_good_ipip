"""v3 Assessment router — 5-demographic + 40-dynamic flow + scoring + content composition."""

from __future__ import annotations

from secrets import token_urlsafe

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from config import settings
from content.careers import get_careers_for_cell
from content.cells import get_cell_content
from database import get_db
from models import Assessment, ShortLink, UserProfile
from questions.demographic import DEMOGRAPHIC_QUESTIONS
from questions.ipip_neo import load_ipip_questions
from questions.holland_riasec import load_riasec_questions
from questions.interest_pool import INTEREST_POOL
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
from services.jwt_service import get_current_user


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
    """Submit all 40 likert answers, score, and compose results."""
    assessment = db.query(Assessment).filter(Assessment.id == payload.assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if assessment.completed:
        raise HTTPException(status_code=400, detail="Already submitted; use GET /results")

    expected_ids = set(qid for qid in (assessment.question_ids or []) if not qid.startswith("DEM_"))
    received_ids = set(payload.answers.keys())
    missing = expected_ids - received_ids
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing answers for {len(missing)} questions: {sorted(missing)[:5]}...",
        )

    likert_answers = {
        k: int(v)
        for k, v in payload.answers.items()
        if isinstance(v, int) or (isinstance(v, str) and v.isdigit())
    }
    riasec = compute_riasec_scores(likert_answers)
    ocean = compute_ocean_scores(likert_answers)
    ocean_pct = compute_ocean_percentiles(ocean)
    holland_code = compute_holland_code(riasec)
    cell_id = derive_archetype_cell(riasec, holland_code)
    mast = check_mast_trigger(ocean_pct, riasec)

    assessment.answers = payload.answers
    assessment.completed = True
    assessment.riasec_scores = riasec
    assessment.ocean_scores = ocean
    assessment.ocean_percentiles = ocean_pct
    assessment.holland_code = holland_code
    assessment.archetype_cell = cell_id

    share_code = token_urlsafe(6)[:8]
    assessment.share_code = share_code
    canonical_url = f"{settings.FRONTEND_URL}/results/{assessment.id}"
    db.add(ShortLink(code=share_code, assessment_id=assessment.id, target_url=canonical_url))
    db.commit()
    db.refresh(assessment)

    return _compose_results_response(assessment, mast)


@router.get("/{assessment_id}/state", response_model=V3AssessmentStartResponse)
def get_assessment_state(assessment_id: str, db: Session = Depends(get_db)):
    """Return the question set + seed for an in-progress assessment so the
    frontend can resume after a page refresh without creating a new row.
    Returns 400 if the assessment is already submitted (use /results instead).
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if assessment.completed:
        raise HTTPException(status_code=400, detail="Assessment already submitted")

    qids = [qid for qid in (assessment.question_ids or []) if not qid.startswith("DEM_")]
    by_id = {q.id: q for q in (*load_riasec_questions(), *load_ipip_questions(), *INTEREST_POOL)}
    questions = [by_id[qid] for qid in qids if qid in by_id]

    return V3AssessmentStartResponse(
        assessment_id=assessment.id,
        questions=[_question_to_payload(q) for q in questions],
        seed=assessment.selection_seed or "",
    )


@router.post("/{assessment_id}/attach-profile")
def attach_profile_to_assessment(
    assessment_id: str,
    db: Session = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """Link a logged-in user (JWT) to this assessment for dashboard / receipts."""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    assessment.profile_session_token = user.session_token
    db.commit()
    return {"ok": True, "assessment_id": assessment_id}


@router.get("/{assessment_id}/results", response_model=V3AssessmentResultResponse)
def get_results(assessment_id: str, db: Session = Depends(get_db)):
    """GET endpoint for re-fetching results after submit. Free 5-screen data only."""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if not assessment.completed:
        raise HTTPException(status_code=400, detail="Assessment not yet submitted")
    # MAST check is stateless; recompute from stored OCEAN + RIASEC
    mast = check_mast_trigger(assessment.ocean_percentiles or {}, assessment.riasec_scores or {})
    return _compose_results_response(assessment, mast)


def _compose_results_response(assessment: Assessment, mast: bool) -> V3AssessmentResultResponse:
    """Build the V3AssessmentResultResponse from a completed Assessment."""
    cell_id = assessment.archetype_cell
    cell_content = get_cell_content(cell_id)

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

    share_url = (
        f"{settings.API_PUBLIC_URL.rstrip('/')}/s/{assessment.share_code}"
        if assessment.share_code
        else ""
    )

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
        holland_radar=assessment.riasec_scores,
        careers_preview=careers_preview,
        share_code=assessment.share_code or "",
        share_url=share_url,
        is_paid=assessment.paid,
        is_mast_trigger=mast,
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
    return V3MilestoneResponse(milestone=milestone, text=get_copy_for_milestone(milestone, seed))
