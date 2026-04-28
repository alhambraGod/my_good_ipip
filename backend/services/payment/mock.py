"""Mock payment driver — always succeeds. For dev / mock-mode."""

from __future__ import annotations

from config import settings
from services.payment.base import PaymentIntent


class MockDriver:
    """Always-succeed driver. Use for tests + local dev (PAYMENT_MODE=mock)."""

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
