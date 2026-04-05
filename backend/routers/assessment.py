"""Assessment router — profile bootstrap, personalized question retrieval, and answer submission."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models import Assessment, UserProfile
from questions.question_bank import get_all_questions, get_question_by_ids, get_question_pool
from schemas import (
    AnswerSubmission,
    AssessmentResponse,
    AssessmentSummary,
    PersonalizedQuestionStartRequest,
    PersonalizedQuestionStartResponse,
    ProfileBootstrapRequest,
    ProfileBootstrapResponse,
    ProfileSupplementRequest,
    ProfileSupplementResponse,
    QuestionOut,
)
from services.jwt_service import get_optional_user
from services.personalization import select_personalized_questions
from services.scoring import calculate_percentiles, calculate_scores, validate_answer_set

router = APIRouter(prefix="/api/assessment", tags=["assessment"])


def _normalize_handle(handle: str | None) -> str | None:
    if not handle:
        return None
    clean = handle.strip()
    if clean.startswith("@"):
        clean = clean[1:]
    return clean or None


def _build_profile_vector(profile: UserProfile, supplement: ProfileSupplementRequest | None = None) -> dict:
    manual = supplement.answers if supplement else (profile.manual_answers or {})
    free_text = supplement.free_text_fields if supplement else {}

    industry = manual.get("industry") or free_text.get("industry") or "general"
    career_stage = manual.get("career_stage") or "early"
    work_mode = manual.get("work_mode") or "hybrid"
    career_goal = manual.get("career_goal") or "growth"
    stress_source = manual.get("stress_source") or "uncertainty"

    scenes = {
        "all",
        "career_switch" if career_goal == "switch" else "fresher",
        industry,
        "remote" if work_mode == "remote" else "enterprise",
    }

    if profile.provider == "x":
        scenes.add("social_media")
    if profile.provider == "telegram":
        scenes.add("community")

    return {
        "industry": industry,
        "career_stage": career_stage,
        "work_mode": work_mode,
        "career_goal": career_goal,
        "stress_source": stress_source,
        "scenes": sorted(list(scenes)),
        "source": profile.provider,
        "personalization_version": settings.PERSONALIZATION_VERSION,
    }


@router.get("/questions", response_model=list[QuestionOut])
def get_questions():
    """Backward-compatible 40-question endpoint."""
    return get_all_questions()


@router.post("/profile/bootstrap", response_model=ProfileBootstrapResponse)
def profile_bootstrap(payload: ProfileBootstrapRequest, db: Session = Depends(get_db)):
    if not payload.consent_flags.get("profile_collection", False):
        raise HTTPException(status_code=400, detail="Profile collection consent is required")

    handle = _normalize_handle(payload.handle)

    prefill_data = {
        "provider": payload.provider,
        "handle": handle,
    }

    needs_manual_questions = payload.provider in {"x", "telegram"}

    if payload.provider == "manual":
        needs_manual_questions = True

    if payload.provider == "x" and handle and settings.X_BEARER_TOKEN:
        prefill_data["public_profile_detected"] = True
    elif payload.provider in {"x", "telegram"} and handle:
        prefill_data["public_profile_detected"] = False

    profile = UserProfile(
        session_token=str(uuid.uuid4()),
        provider=payload.provider,
        external_handle=handle,
        external_public_data=prefill_data if payload.provider in {"x", "telegram"} else None,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    return ProfileBootstrapResponse(
        session_token=profile.session_token,
        prefill_data=prefill_data,
        needs_manual_questions=needs_manual_questions,
    )


@router.post("/profile/supplement", response_model=ProfileSupplementResponse)
def profile_supplement(payload: ProfileSupplementRequest, db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.session_token == payload.session_token).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile session not found")

    profile.manual_answers = payload.answers
    profile.profile_vector = _build_profile_vector(profile, payload)
    db.commit()

    total_fields = 6
    filled = sum(
        1
        for key in ["industry", "career_stage", "work_mode", "career_goal", "stress_source", "communication_style"]
        if payload.answers.get(key) or payload.free_text_fields.get(key)
    )
    completeness = round(filled / total_fields, 2)

    return ProfileSupplementResponse(profile_vector=profile.profile_vector, completeness=completeness)


@router.get("/{assessment_id}/questions", response_model=list[QuestionOut])
def get_personalized_questions(assessment_id: str, db: Session = Depends(get_db)):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    if not assessment.question_ids:
        raise HTTPException(status_code=400, detail="Assessment has no personalized question set")

    return get_question_by_ids(assessment.question_ids)


@router.post("/start-personalized", response_model=PersonalizedQuestionStartResponse)
def start_personalized(payload: PersonalizedQuestionStartRequest, db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.session_token == payload.session_token).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile session not found")

    if not profile.profile_vector:
        profile.profile_vector = _build_profile_vector(profile)
        db.commit()

    seed = str(uuid.uuid4())
    pool = get_question_pool(settings.QUESTION_BANK_VERSION)
    selected_questions = select_personalized_questions(profile.profile_vector, pool, seed)
    selected_ids = [q["id"] for q in selected_questions]

    assessment = Assessment(
        completed=False,
        paid=False,
        profile_source=profile.provider,
        profile_data=profile.profile_vector,
        question_set_version=settings.QUESTION_BANK_VERSION,
        question_ids=selected_ids,
        selection_seed=seed,
        profile_session_token=profile.session_token,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    return PersonalizedQuestionStartResponse(
        assessment_id=assessment.id,
        questions=selected_questions,
        question_ids=selected_ids,
    )


@router.post("/submit", response_model=AssessmentResponse)
def submit_assessment(submission: AnswerSubmission, db: Session = Depends(get_db)):
    """Submit answers, calculate scores, return assessment ID."""
    if submission.assessment_id:
        assessment = db.query(Assessment).filter(Assessment.id == submission.assessment_id).first()
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")

        expected_ids = assessment.question_ids or []
        if len(expected_ids) != 40:
            raise HTTPException(status_code=400, detail="Invalid assessment question set")

        try:
            validate_answer_set(submission.answers, expected_ids)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        scores = calculate_scores(submission.answers)
        percentiles = calculate_percentiles(scores)

        assessment.answers = submission.answers
        assessment.scores = scores
        assessment.percentiles = percentiles
        assessment.completed = True
        db.commit()
        db.refresh(assessment)

        return AssessmentResponse(
            id=assessment.id,
            completed=True,
            paid=assessment.paid,
            scores=scores,
            percentiles=percentiles,
        )

    # Legacy path
    if len(submission.answers) < 40:
        raise HTTPException(status_code=400, detail=f"Expected 40 answers, got {len(submission.answers)}")

    scores = calculate_scores(submission.answers)
    percentiles = calculate_percentiles(scores)

    assessment = Assessment(
        answers=submission.answers,
        scores=scores,
        percentiles=percentiles,
        completed=True,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    return AssessmentResponse(
        id=assessment.id,
        completed=True,
        paid=False,
        scores=scores,
        percentiles=percentiles,
    )


@router.get("/my-assessments", response_model=list[AssessmentSummary])
def list_my_assessments(
    session_token: str | None = None,
    user: UserProfile | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """Return all assessments belonging to the user, newest first.
    Accepts JWT Bearer token or session_token query param for backwards compat.
    """
    profile = user
    if not profile and session_token:
        profile = db.query(UserProfile).filter(UserProfile.session_token == session_token).first()
    if not profile:
        raise HTTPException(status_code=401, detail="Authentication required")

    assessments = (
        db.query(Assessment)
        .filter(Assessment.profile_session_token == profile.session_token)
        .order_by(Assessment.created_at.desc())
        .all()
    )

    return [
        AssessmentSummary(
            id=a.id,
            created_at=a.created_at.isoformat() if a.created_at else "",
            completed=a.completed,
            paid=a.paid,
            scores=a.scores,
            has_report=bool(a.report_html),
        )
        for a in assessments
    ]


@router.get("/{assessment_id}", response_model=AssessmentResponse)
def get_assessment(assessment_id: str, db: Session = Depends(get_db)):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    return AssessmentResponse(
        id=assessment.id,
        completed=assessment.completed,
        paid=assessment.paid,
        scores=assessment.scores,
        percentiles=assessment.percentiles,
    )
