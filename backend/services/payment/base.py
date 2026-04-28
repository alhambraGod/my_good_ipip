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
