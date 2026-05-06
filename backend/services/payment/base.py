"""Payment driver abstract interface.

Every concrete driver (Razorpay, Cashfree, PayU, UPI Intent, Mock,
Stripe) implements this Protocol so the rest of the app can swap
providers without code changes.

See `docs/PAYMENT_PROVIDERS.md` for the full landscape research and
selection rubric. See `factory.py` for the registry / selector.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol

PaymentProvider = Literal[
    "mock",
    "razorpay",
    "cashfree",
    "payu",
    "upi",          # direct UPI Intent (no aggregator)
    "stripe",       # international fallback
    "wechat",       # backlogged
]


@dataclass(frozen=True)
class PaymentIntent:
    """Result of creating a payment intent.

    A single shape across drivers — the frontend decides how to use it
    based on `provider`:

    * `payment_url`           — the URL to redirect the browser to.
                                For SDK-modal drivers (Razorpay/Cashfree)
                                this can be a fallback URL, with the
                                preferred path being the `client_payload`.
    * `client_payload`        — JSON-serialisable opts the frontend SDK
                                consumes to open an in-page modal.
    * `txn_id`                — the provider's order/intent id we record
                                on the assessment row (for verify + webhook
                                matching).
    * `qr_code_data_url`      — present for UPI Intent driver (PNG data
                                URL); None otherwise.
    """
    provider: PaymentProvider
    assessment_id: str
    amount_inr: int
    payment_url: str
    txn_id: str | None = None
    client_payload: dict | None = None
    qr_code_data_url: str | None = None
    raw_response: dict | None = None


@dataclass(frozen=True)
class ProviderInfo:
    """Public metadata about a payment driver — surfaced to the frontend.

    The picker UI on `/payment` reads `GET /api/v3/payment/providers`
    which returns a list of these.
    """
    id: PaymentProvider
    label_en: str
    label_hi: str
    description_en: str
    supports_methods: tuple[str, ...] = field(default_factory=tuple)  # e.g. ("UPI", "Card", "NetBanking")
    requires_redirect: bool = False     # form-POST drivers (PayU) need this
    recommended: bool = False           # checkmark in the UI
    enabled: bool = True


class PaymentDriver(Protocol):
    """Strategy interface for payment providers.

    All methods are sync; HTTP-bound drivers use httpx.Client which has
    its own timeout. Webhook + checkout signature verification is split
    so a single driver can serve both flows.
    """

    @property
    def provider_name(self) -> PaymentProvider: ...

    @property
    def info(self) -> ProviderInfo: ...

    def create_payment_intent(self, assessment_id: str, amount_inr: int) -> PaymentIntent: ...

    def verify_payment(self, txn_id: str | None) -> bool: ...

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool: ...
