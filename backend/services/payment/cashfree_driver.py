"""Cashfree Payments driver — Indian aggregator, Order API + JS SDK.

Reference: https://docs.cashfree.com/docs/order-create
JS SDK:    https://sdk.cashfree.com/js/v3/cashfree.js
Webhooks:  HMAC-SHA256(timestamp + raw_body, webhook_secret), base64-encoded.
"""

from __future__ import annotations

import base64
import hashlib
import hmac

import httpx

import config
from services.payment.base import PaymentIntent, ProviderInfo


class CashfreeDriver:
    """Cashfree Payments driver. UPI + Cards + NetBanking via in-page SDK."""

    provider_name = "cashfree"

    @property
    def info(self) -> ProviderInfo:
        return ProviderInfo(
            id="cashfree",
            label_en="UPI / Card (Cashfree)",
            label_hi="UPI / Card (Cashfree)",
            description_en="Cashfree-hosted in-page checkout. Fast UPI on mobile.",
            supports_methods=("UPI", "Card", "NetBanking", "Wallet"),
            requires_redirect=False,
            recommended=False,
            enabled=True,
        )

    def __init__(self) -> None:
        s = config.settings
        if not s.CASHFREE_CLIENT_ID or not s.CASHFREE_CLIENT_SECRET:
            raise ValueError(
                "CASHFREE_CLIENT_ID + CASHFREE_CLIENT_SECRET must be set "
                "(see env/<env>.env)"
            )

    def _api_base(self) -> str:
        return config.settings.CASHFREE_API_BASE.rstrip("/")

    def _headers(self) -> dict:
        s = config.settings
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "x-api-version": "2023-08-01",
            "x-client-id": s.CASHFREE_CLIENT_ID,
            "x-client-secret": s.CASHFREE_CLIENT_SECRET,
        }

    def create_payment_intent(self, assessment_id: str, amount_inr: int) -> PaymentIntent:
        s = config.settings
        # Cashfree Orders API — order_id must be unique per merchant.
        # We prefix with assessment_id so the inverse lookup is trivial.
        order_id = f"mp_{assessment_id[:32]}_{int(amount_inr * 100)}"
        payload = {
            "order_id": order_id,
            "order_amount": amount_inr,
            "order_currency": "INR",
            "customer_details": {
                "customer_id": assessment_id,
                "customer_phone": "9999999999",  # Cashfree requires non-empty; user fills real one in modal
                "customer_email": "user@mindprism.in",
            },
            "order_meta": {
                "return_url": f"{s.FRONTEND_URL}/payment/success?assessment_id={assessment_id}&provider=cashfree",
                "notify_url": f"{s.API_PUBLIC_URL}/api/v3/payment/webhook/cashfree",
            },
            "order_note": f"MindPrism report — {assessment_id[:8]}",
        }
        with httpx.Client(timeout=15.0) as client:
            r = client.post(f"{self._api_base()}/pg/orders", headers=self._headers(), json=payload)
            r.raise_for_status()
            data = r.json()

        return PaymentIntent(
            provider="cashfree",
            assessment_id=assessment_id,
            amount_inr=amount_inr,
            txn_id=data.get("order_id", order_id),
            payment_url=data.get("payment_link") or f"{s.FRONTEND_URL}/payment/success?assessment_id={assessment_id}&provider=cashfree",
            client_payload={
                "payment_session_id": data.get("payment_session_id"),
                "order_id": data.get("order_id"),
                "mode": "production" if "api.cashfree.com" in self._api_base() else "sandbox",
            },
            raw_response=data,
        )

    def verify_payment(self, txn_id: str | None) -> bool:
        if not txn_id:
            return False
        with httpx.Client(timeout=15.0) as client:
            r = client.get(
                f"{self._api_base()}/pg/orders/{txn_id}",
                headers=self._headers(),
            )
            if r.status_code != 200:
                return False
            data = r.json()
        return data.get("order_status") == "PAID"

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Cashfree webhook signature is base64(HMAC-SHA256(timestamp + body, secret)).

        The header carries `x-webhook-signature` and `x-webhook-timestamp`.
        Our payment_v3 webhook handler concatenates them as `signature` arg
        when calling this, in the form `<timestamp>:<sig>` so we can verify
        without needing two header args.
        """
        secret = config.settings.CASHFREE_WEBHOOK_SECRET
        if not secret or ":" not in signature:
            return False
        timestamp, sig = signature.split(":", 1)
        body = (timestamp + payload.decode("utf-8")).encode()
        digest = hmac.new(secret.encode(), body, hashlib.sha256).digest()
        expected = base64.b64encode(digest).decode()
        return hmac.compare_digest(expected, sig)
