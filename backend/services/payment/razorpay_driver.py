"""Razorpay payment driver — India production via payment-link API."""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass

import httpx

import config  # late-binding access to config.settings (survives importlib.reload in tests)
from services.payment.base import PaymentIntent, ProviderInfo

_RAZORPAY_BASE = "https://api.razorpay.com/v1"


@dataclass(frozen=True)
class RazorpayOrder:
    """Result of creating a Razorpay Order, used by the in-page Checkout SDK."""
    order_id: str
    amount_paise: int
    currency: str
    key_id: str
    raw_response: dict | None = None


class RazorpayDriver:
    """Razorpay driver — uses payment_links API for hosted checkout.

    Razorpay accepts amount in PAISE (INR × 100). UI strings remain in lakh,
    but the API requires paise integers.
    """

    provider_name = "razorpay"

    @property
    def info(self) -> ProviderInfo:
        return ProviderInfo(
            id="razorpay",
            label_en="UPI / Card / NetBanking (Razorpay)",
            label_hi="UPI / Card / NetBanking (Razorpay)",
            description_en="Recommended. UPI, cards, netbanking, wallets — all in one in-page modal. Trusted by Razorpay-backed Indian SaaS.",
            supports_methods=("UPI", "Card", "NetBanking", "Wallet"),
            requires_redirect=False,
            recommended=True,
            enabled=True,
        )

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
            "description": "MindPrism Personality Report",
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

    # -------------------------------------------------------------------------
    # Razorpay Standard Checkout (in-page modal) — alternative to payment_links.
    # Frontend opens checkout.razorpay.com SDK with the returned order_id +
    # public key_id; on success, the SDK calls back with the signed handle that
    # we verify via verify_checkout_signature().
    # -------------------------------------------------------------------------

    def create_order(self, assessment_id: str, amount_inr: int) -> RazorpayOrder:
        """Create a Razorpay Order for use with the Checkout JS SDK.

        Note: amounts must be sent in paise (INR × 100).
        """
        amount_paise = amount_inr * 100
        payload = {
            "amount": amount_paise,
            "currency": "INR",
            "receipt": assessment_id[:40],
            "notes": {"assessment_id": assessment_id},
            "payment_capture": 1,
        }
        with httpx.Client(timeout=15.0) as client:
            r = client.post(f"{_RAZORPAY_BASE}/orders", auth=self._auth(), json=payload)
            r.raise_for_status()
            data = r.json()
        return RazorpayOrder(
            order_id=data["id"],
            amount_paise=amount_paise,
            currency="INR",
            key_id=config.settings.RAZORPAY_KEY_ID,
            raw_response=data,
        )

    def verify_checkout_signature(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> bool:
        """Verify the HMAC-SHA256 signature returned by the Razorpay Checkout SDK.

        Spec: signature = HMAC_SHA256(order_id + "|" + payment_id, key_secret)
        """
        secret = config.settings.RAZORPAY_KEY_SECRET
        if not secret or not razorpay_order_id or not razorpay_payment_id or not razorpay_signature:
            return False
        body = f"{razorpay_order_id}|{razorpay_payment_id}".encode()
        expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, razorpay_signature)
