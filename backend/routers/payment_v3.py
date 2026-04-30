"""v3 Payment router — Razorpay-aware with mock fallback + webhook handler + promo pricing."""

from __future__ import annotations

import json
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

import config
from database import get_db
from models import Assessment
from schemas import V3PaymentIntentRequest, V3PaymentIntentResponse
from services.payment.factory import get_payment_driver
from services.payment.razorpay_driver import RazorpayDriver


class RazorpayCheckoutOrderResponse(BaseModel):
    assessment_id: str
    provider: Literal["razorpay", "mock"]
    order_id: str | None
    amount_inr: int
    amount_paise: int
    currency: str
    key_id: str | None
    promo_active: bool
    # Mock-only convenience: the same redirect URL that create-intent returns,
    # so the frontend can fall back when Razorpay isn't configured.
    mock_redirect_url: str | None = None


class RazorpayCheckoutVerifyRequest(BaseModel):
    assessment_id: str
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


router = APIRouter(prefix="/api/v3/payment", tags=["payment_v3"])


def _current_price(db: Session) -> tuple[int, bool, int]:
    """Return (amount_inr, promo_active, promo_remaining) based on confirmed-paid count vs cap."""
    paid_count = db.query(Assessment).filter(Assessment.payment_status == "confirmed").count()
    cap = config.settings.PROMO_MAX_REDEMPTIONS
    remaining = max(cap - paid_count, 0)
    if paid_count < cap:
        return config.settings.PRICE_PROMO_INR, True, remaining
    return config.settings.PRICE_FULL_INR, False, 0


@router.get("/price")
def get_price(db: Session = Depends(get_db)):
    """Public price preview: current INR amount + promo metadata.

    Used by the payment page to render real numbers BEFORE the user clicks pay.
    """
    amount_inr, promo_active, promo_remaining = _current_price(db)
    return {
        "amount_inr": amount_inr,
        "promo_active": promo_active,
        "promo_remaining": promo_remaining,
        "price_full_inr": config.settings.PRICE_FULL_INR,
        "price_promo_inr": config.settings.PRICE_PROMO_INR,
        "promo_cap": config.settings.PROMO_MAX_REDEMPTIONS,
    }


@router.post("/create-intent", response_model=V3PaymentIntentResponse)
def create_intent(payload: V3PaymentIntentRequest, db: Session = Depends(get_db)):
    """Create a payment intent (Razorpay payment link or mock URL).

    Validates the assessment is completed and not yet paid, then delegates to the
    configured PaymentDriver. Persists provider, txn_id, amount, and pending status.
    """
    assessment = db.query(Assessment).filter(Assessment.id == payload.assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if not assessment.completed:
        raise HTTPException(status_code=400, detail="Assessment not yet completed")
    if assessment.paid:
        raise HTTPException(status_code=400, detail="Already paid")

    amount_inr, promo_active, _remaining = _current_price(db)
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


@router.post("/razorpay/order", response_model=RazorpayCheckoutOrderResponse)
def create_razorpay_order(
    payload: V3PaymentIntentRequest,
    db: Session = Depends(get_db),
):
    """Create a Razorpay Order suitable for the in-page Checkout JS SDK.

    When PAYMENT_MODE=mock, returns a stub response with a redirect URL the
    frontend can use as fallback (matching the existing /payment/success flow).
    """
    assessment = db.query(Assessment).filter(Assessment.id == payload.assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if not assessment.completed:
        raise HTTPException(status_code=400, detail="Assessment not yet completed")
    if assessment.paid:
        raise HTTPException(status_code=400, detail="Already paid")

    amount_inr, promo_active, _remaining = _current_price(db)

    if config.settings.PAYMENT_MODE != "razorpay":
        # Re-use mock driver to get a redirect URL
        driver = get_payment_driver()
        intent = driver.create_payment_intent(assessment.id, amount_inr=amount_inr)
        assessment.payment_provider = intent.provider
        assessment.payment_txn_id = intent.txn_id
        assessment.payment_amount_inr = amount_inr
        assessment.payment_status = "pending"
        db.commit()
        return RazorpayCheckoutOrderResponse(
            assessment_id=assessment.id,
            provider="mock",
            order_id=None,
            amount_inr=amount_inr,
            amount_paise=amount_inr * 100,
            currency="INR",
            key_id=None,
            promo_active=promo_active,
            mock_redirect_url=intent.payment_url,
        )

    rzp = RazorpayDriver()
    order = rzp.create_order(assessment.id, amount_inr=amount_inr)
    assessment.payment_provider = "razorpay"
    assessment.payment_txn_id = order.order_id
    assessment.payment_amount_inr = amount_inr
    assessment.payment_status = "pending"
    db.commit()

    return RazorpayCheckoutOrderResponse(
        assessment_id=assessment.id,
        provider="razorpay",
        order_id=order.order_id,
        amount_inr=amount_inr,
        amount_paise=order.amount_paise,
        currency=order.currency,
        key_id=order.key_id,
        promo_active=promo_active,
    )


@router.post("/razorpay/verify")
def verify_razorpay_checkout(
    payload: RazorpayCheckoutVerifyRequest,
    db: Session = Depends(get_db),
):
    """Verify the HMAC signature returned by the Razorpay Checkout SDK on success.

    Marks the assessment as paid + confirmed when the signature matches.
    """
    assessment = db.query(Assessment).filter(Assessment.id == payload.assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if assessment.payment_provider != "razorpay" or assessment.payment_txn_id != payload.razorpay_order_id:
        raise HTTPException(status_code=400, detail="Order does not match assessment")

    rzp = RazorpayDriver()
    if not rzp.verify_checkout_signature(
        razorpay_order_id=payload.razorpay_order_id,
        razorpay_payment_id=payload.razorpay_payment_id,
        razorpay_signature=payload.razorpay_signature,
    ):
        raise HTTPException(status_code=401, detail="Invalid Razorpay signature")

    if not assessment.paid:
        assessment.paid = True
        assessment.payment_status = "confirmed"
        db.commit()

    return {"assessment_id": assessment.id, "paid": True, "status": "confirmed"}


@router.post("/webhook/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """Razorpay webhook handler — verifies signature, marks assessment paid on payment_link.paid."""
    raw_body = await request.body()
    driver = get_payment_driver()
    if not driver.verify_webhook_signature(raw_body, x_razorpay_signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        event = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_name = event.get("event", "")
    if event_name == "payment_link.paid":
        try:
            link_id = event["payload"]["payment_link"]["entity"]["id"]
        except (KeyError, TypeError):
            raise HTTPException(status_code=400, detail="Malformed payment_link.paid payload")

        assessment = db.query(Assessment).filter(Assessment.payment_txn_id == link_id).first()
        if assessment and assessment.payment_status != "confirmed":
            assessment.paid = True
            assessment.payment_status = "confirmed"
            db.commit()

    return {"received": True, "event": event_name}


@router.get("/verify/{assessment_id}")
def verify_payment(assessment_id: str, db: Session = Depends(get_db)):
    """Polling endpoint for clients to check payment status.

    For mock mode: always succeeds (verify_payment returns True).
    For Razorpay: polls the payment-link status; returns paid=True if Razorpay confirms.
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    if assessment.payment_status == "pending" and assessment.payment_txn_id is not None:
        driver = get_payment_driver()
        if driver.verify_payment(assessment.payment_txn_id):
            assessment.paid = True
            assessment.payment_status = "confirmed"
            db.commit()
    elif assessment.payment_status == "pending" and assessment.payment_provider == "mock":
        # Mock without txn_id (created intent in mock mode) — also confirm
        driver = get_payment_driver()
        if driver.verify_payment(None):
            assessment.paid = True
            assessment.payment_status = "confirmed"
            db.commit()

    return {
        "assessment_id": assessment_id,
        "paid": assessment.paid,
        "status": assessment.payment_status,
    }
