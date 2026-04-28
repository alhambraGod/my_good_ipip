"""Razorpay payment driver — India production via payment-link API."""

from __future__ import annotations

import hashlib
import hmac

import httpx

import config  # late-binding access to config.settings (survives importlib.reload in tests)
from services.payment.base import PaymentIntent

_RAZORPAY_BASE = "https://api.razorpay.com/v1"


class RazorpayDriver:
    """Razorpay driver — uses payment_links API for hosted checkout.

    Razorpay accepts amount in PAISE (INR × 100). UI strings remain in lakh,
    but the API requires paise integers.
    """

    provider_name = "razorpay"

    def __init__(self) -> None:
        s = config.settings
        if not s.RAZORPAY_KEY_ID or not s.RAZORPAY_KEY_SECRET:
            raise ValueError(
                "RAZORPAY_KEY_ID + RAZORPAY_KEY_SECRET must be set in env "
                "(check env/<env>.env or set PAYMENT_MODE=mock for dev)"
            )

    def _auth(self) -> tuple[str, str]:
        s = config.settings
        return (s.RAZORPAY_KEY_ID, s.RAZORPAY_KEY_SECRET)

    def create_payment_intent(self, assessment_id: str, amount_inr: int) -> PaymentIntent:
        amount_paise = amount_inr * 100
        payload = {
            "amount": amount_paise,
            "currency": "INR",
            "accept_partial": False,
            "description": "CareerDNA Personality Report",
            "notify": {"email": True, "sms": True},
            "reminder_enable": True,
            "callback_url": f"{config.settings.FRONTEND_URL}/payment/success?assessment_id={assessment_id}",
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
        secret = config.settings.RAZORPAY_WEBHOOK_SECRET
        if not secret:
            return False
        expected = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
