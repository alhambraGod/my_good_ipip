"""v3 Payment router — multi-provider (Razorpay + Cashfree + PayU + UPI Intent + Mock)."""

from __future__ import annotations

import json
import logging
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

import config
from database import get_db
from models import Assessment
from schemas import V3PaymentIntentRequest, V3PaymentIntentResponse
from services.payment.factory import (
    DRIVER_FACTORIES,
    default_driver_id,
    get_payment_driver,
    list_provider_infos,
)
from services.payment.razorpay_driver import RazorpayDriver

log = logging.getLogger(__name__)


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


@router.get("/providers")
def get_providers():
    """Return the list of payment drivers the operator has enabled.

    Each entry has UI metadata (label, label_hi, description, supported
    methods) plus a `recommended` flag (set on the default driver).
    The frontend's `<PaymentMethodPicker />` uses this to render chips.
    """
    infos = list_provider_infos()
    default_id = default_driver_id()
    return {
        "default": default_id,
        "providers": [
            {
                "id": p.id,
                "label_en": p.label_en,
                "label_hi": p.label_hi,
                "description_en": p.description_en,
                "supports_methods": list(p.supports_methods),
                "requires_redirect": p.requires_redirect,
                "recommended": p.recommended,
                "enabled": p.enabled,
            }
            for p in infos
        ],
    }


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


class V3CreateIntentRequest(BaseModel):
    assessment_id: str
    provider: str | None = None      # if absent, the default driver is used


@router.post("/create-intent", response_model=V3PaymentIntentResponse)
def create_intent(payload: V3CreateIntentRequest, db: Session = Depends(get_db)):
    """Generic create-payment-intent — picks the requested driver.

    Validates the assessment is completed and not yet paid, then delegates
    to the chosen `PaymentDriver`. Persists provider, txn_id, amount, and
    pending status. The response now also includes the driver's
    `client_payload` (e.g. Razorpay order_id + key, Cashfree
    payment_session_id, UPI deep link + QR PNG data URL) so the frontend
    SDK / picker can drive the modal in-page.
    """
    assessment = db.query(Assessment).filter(Assessment.id == payload.assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if not assessment.completed:
        raise HTTPException(status_code=400, detail="Assessment not yet completed")
    if assessment.paid:
        raise HTTPException(status_code=400, detail="Already paid")

    amount_inr, promo_active, _remaining = _current_price(db)
    try:
        driver = get_payment_driver(payload.provider)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    try:
        intent = driver.create_payment_intent(assessment.id, amount_inr=amount_inr)
    except Exception as exc:
        log.exception("create_payment_intent failed for %s", driver.provider_name)
        raise HTTPException(status_code=502, detail=f"Provider {driver.provider_name} unavailable: {exc}")

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
        txn_id=intent.txn_id,
        client_payload=intent.client_payload,
        qr_code_data_url=intent.qr_code_data_url,
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

    if "razorpay" not in {p.id for p in list_provider_infos()}:
        # Re-use mock/default driver to get a redirect URL
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


def _mark_paid_by_txn_id(db: Session, txn_id: str | None) -> bool:
    """Look up an assessment by stored payment_txn_id and confirm it. Returns True if updated."""
    if not txn_id:
        return False
    assessment = db.query(Assessment).filter(Assessment.payment_txn_id == txn_id).first()
    if assessment and assessment.payment_status != "confirmed":
        assessment.paid = True
        assessment.payment_status = "confirmed"
        db.commit()
        return True
    return False


class UPIConfirmRequest(BaseModel):
    assessment_id: str
    txn_ref: str | None = None         # echoes Intent.txn_id (for human ops)
    user_remark: str | None = None     # free-text "transaction id from my UPI app"


@router.post("/upi/confirm")
def confirm_upi_payment(payload: UPIConfirmRequest, db: Session = Depends(get_db)):
    """User-driven confirmation for the UPI Intent flow.

    The UPI Intent driver has no automated callback — once the user pays
    via their UPI app, they tap "I've paid" and we mark the assessment
    `payment_status="awaiting_review"`. Operations confirms by matching
    against the bank statement (manual SLA: 30 minutes during business
    hours) and POSTs `/api/v3/payment/admin/upi/confirm` (separate
    auth-protected admin endpoint, not exposed here in v1).
    """
    assessment = db.query(Assessment).filter(Assessment.id == payload.assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if assessment.payment_provider != "upi":
        raise HTTPException(status_code=400, detail="Not a UPI assessment")
    if assessment.paid:
        return {"assessment_id": assessment.id, "paid": True, "status": "confirmed"}
    assessment.payment_status = "awaiting_review"
    if payload.user_remark:
        # Save as last note for ops; don't shadow txn_id which is our ref.
        assessment.report_data = {
            **(assessment.report_data or {}),
            "upi_user_remark": payload.user_remark[:200],
        }
    db.commit()
    return {
        "assessment_id": assessment.id,
        "paid": False,
        "status": "awaiting_review",
        "message": "Payment received notice — operations will confirm shortly.",
    }


@router.post("/webhook/cashfree")
async def cashfree_webhook(
    request: Request,
    x_webhook_signature: str = Header(default=""),
    x_webhook_timestamp: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """Cashfree webhook handler.

    Cashfree signs `HMAC_SHA256(timestamp + raw_body, secret)`, base64-encoded;
    we pass `timestamp:signature` to the driver since Protocol exposes only
    a single string arg.
    """
    from services.payment.cashfree_driver import CashfreeDriver

    raw = await request.body()
    if not x_webhook_signature or not x_webhook_timestamp:
        raise HTTPException(status_code=400, detail="Missing webhook headers")
    try:
        driver = CashfreeDriver()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Cashfree not configured: {exc}")
    if not driver.verify_webhook_signature(
        raw, f"{x_webhook_timestamp}:{x_webhook_signature}"
    ):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        event = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    matched = False
    try:
        order = event.get("data", {}).get("order", {})
        order_id = order.get("order_id")
        if event.get("type") in ("PAYMENT_SUCCESS_WEBHOOK", "ORDER_PAID") and order_id:
            matched = _mark_paid_by_txn_id(db, order_id)
    except (KeyError, TypeError):
        raise HTTPException(status_code=400, detail="Malformed Cashfree payload")
    return {"received": True, "matched": matched}


@router.post("/webhook/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """Razorpay webhook handler — verifies signature and marks the assessment paid.

    Supports BOTH payment-link flow (legacy) and Order/Checkout-SDK flow:

    * ``payment_link.paid``      — payload.payment_link.entity.id matches stored txn_id
    * ``order.paid``             — payload.order.entity.id        matches stored txn_id
    * ``payment.captured``       — payload.payment.entity.order_id matches stored txn_id
                                  (also payload.payment.entity.payment_link_id, if present)

    Other events are accepted (200) but ignored — Razorpay otherwise retries them aggressively.
    """
    raw_body = await request.body()
    driver = get_payment_driver()
    if not driver.verify_webhook_signature(raw_body, x_razorpay_signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        event = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_name = event.get("event", "")
    payload_root = event.get("payload", {}) or {}
    matched = False

    try:
        if event_name == "payment_link.paid":
            link_id = payload_root["payment_link"]["entity"]["id"]
            matched = _mark_paid_by_txn_id(db, link_id)

        elif event_name == "order.paid":
            order_id = payload_root["order"]["entity"]["id"]
            matched = _mark_paid_by_txn_id(db, order_id)

        elif event_name == "payment.captured":
            payment_entity = payload_root["payment"]["entity"]
            order_id = payment_entity.get("order_id")
            link_id = payment_entity.get("payment_link_id")
            for txn_id in (order_id, link_id):
                if _mark_paid_by_txn_id(db, txn_id):
                    matched = True
                    break
    except (KeyError, TypeError):
        raise HTTPException(status_code=400, detail=f"Malformed {event_name} payload")

    return {"received": True, "event": event_name, "matched": matched}


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
