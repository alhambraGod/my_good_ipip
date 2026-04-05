"""Payment router — Stripe checkout + mock payment."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models import Assessment, UserProfile
from schemas import PaymentCreateResponse, PaymentVerifyResponse
from services.payment_service import create_checkout_session, verify_payment

router = APIRouter(prefix="/api/payment", tags=["payment"])


def _is_dev_assessment(assessment: Assessment, db: Session) -> bool:
    if not settings.DEV_ACCOUNT_ENABLED:
        return False
    if not assessment.profile_session_token:
        return False

    profile = (
        db.query(UserProfile)
        .filter(
            UserProfile.session_token == assessment.profile_session_token,
            UserProfile.is_dev_account.is_(True),
        )
        .first()
    )
    return profile is not None


@router.post("/create-session/{assessment_id}", response_model=PaymentCreateResponse)
def create_payment(assessment_id: str, db: Session = Depends(get_db)):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if not assessment.completed:
        raise HTTPException(status_code=400, detail="Assessment not completed")

    if _is_dev_assessment(assessment, db):
        return PaymentCreateResponse(
            checkout_url=f"{settings.FRONTEND_URL}/payment/success?assessment_id={assessment_id}&mock=true",
            mock=True,
            assessment_id=assessment_id,
        )

    if assessment.paid:
        raise HTTPException(status_code=400, detail="Already paid")

    result = create_checkout_session(assessment_id)
    if not result.get("mock"):
        assessment.stripe_session_id = result.get("session_id")
        db.commit()

    return PaymentCreateResponse(**result)


@router.get("/verify", response_model=PaymentVerifyResponse)
def verify(
    assessment_id: str = Query(...),
    session_id: str = Query(None),
    mock: bool = Query(False),
    db: Session = Depends(get_db),
):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    if assessment.paid:
        return PaymentVerifyResponse(paid=True, assessment_id=assessment_id)

    if _is_dev_assessment(assessment, db):
        assessment.paid = True
        db.commit()
        return PaymentVerifyResponse(paid=True, assessment_id=assessment_id)

    is_paid = verify_payment(session_id, mock)
    if is_paid:
        assessment.paid = True
        db.commit()

    return PaymentVerifyResponse(paid=is_paid, assessment_id=assessment_id)
