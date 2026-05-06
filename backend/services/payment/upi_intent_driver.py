"""UPI Intent driver — pure NPCI deep link, no aggregator.

This driver builds an `upi://pay?...` deep link that mobile users can
tap to open their preferred UPI app (PhonePe / Google Pay / Paytm /
BHIM); desktop users see the same URL rendered as a QR code that they
scan with their phone.

There is **no automated payment confirmation** — the user clicks
"I've paid" on the success page, and operations either:

  * polls their bank's incoming-txn API (when available), or
  * matches the txn-ref against the merchant's bank statement manually.

Why ship this anyway?
  * Onboarding is instant — you only need a working UPI VPA (no aggregator KYC).
  * Settlement is direct (₹49 minus 0 fees lands in your bank).
  * Great for Tier-2/3 users where Razorpay's modal sometimes feels heavy.

For higher trust, pair this with a second "Razorpay" path; Razorpay
is recommended by default in the picker, UPI is the "free / no
account" option.

NPCI deep-link spec:
    https://www.npci.org.in/PDF/npci/upi/circular/2017/UPI-LinkingSpecsver1.6.pdf

Deep-link grammar:
    upi://pay?pa=<vpa>&pn=<name>&am=<amount>&cu=INR&tn=<note>&tr=<ref>
"""

from __future__ import annotations

import base64
import io
import secrets
from urllib.parse import quote

import config
from services.payment.base import PaymentIntent, ProviderInfo


def _build_qr_png_data_url(text: str) -> str | None:
    """Render `text` as a PNG QR code, return a data URL.

    Uses the optional `segno` lib (pure Python, no native deps); if it's
    not installed, returns None so the caller falls back to the plain
    deep link.
    """
    try:
        import segno  # type: ignore
    except ImportError:
        return None
    qr = segno.make(text, error="m")
    buf = io.BytesIO()
    qr.save(buf, kind="png", scale=6, dark="#1A202C", light="#FFFAF0")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


class UPIIntentDriver:
    """Direct UPI deep-link / QR driver — manual confirmation.

    Configuration: ``UPI_VPA`` (your business VPA) + ``UPI_DISPLAY_NAME``.
    No webhook, no API auth — purely a URL builder.
    """

    provider_name = "upi"

    @property
    def info(self) -> ProviderInfo:
        s = config.settings
        return ProviderInfo(
            id="upi",
            label_en="UPI Pay (PhonePe / GPay / Paytm)",
            label_hi="UPI se pay karo",
            description_en=(
                f"Pay ₹{s.PRICE_PROMO_INR}–{s.PRICE_FULL_INR} via your favourite UPI app. "
                f"You'll click 'I've paid' to unlock — typically confirmed within 60 seconds."
            ),
            supports_methods=("UPI",),
            requires_redirect=False,
            recommended=False,
            enabled=True,
        )

    def __init__(self) -> None:
        s = config.settings
        if not s.UPI_VPA:
            raise ValueError(
                "UPI_VPA must be set (e.g. UPI_VPA=mindprism@hdfcbank); "
                "see env/<env>.env"
            )

    def create_payment_intent(self, assessment_id: str, amount_inr: int) -> PaymentIntent:
        s = config.settings
        txn_ref = f"MIND{secrets.token_hex(4).upper()}"
        params = (
            f"pa={quote(s.UPI_VPA)}"
            f"&pn={quote(s.UPI_DISPLAY_NAME or 'MindPrism')}"
            f"&am={amount_inr:.2f}"
            f"&cu=INR"
            f"&tn={quote(f'MindPrism {assessment_id[:8]}')}"
            f"&tr={quote(txn_ref)}"
        )
        deep_link = f"upi://pay?{params}"
        qr_png = _build_qr_png_data_url(deep_link)

        return PaymentIntent(
            provider="upi",
            assessment_id=assessment_id,
            amount_inr=amount_inr,
            txn_id=txn_ref,
            payment_url=deep_link,
            qr_code_data_url=qr_png,
            client_payload={
                "vpa": s.UPI_VPA,
                "display_name": s.UPI_DISPLAY_NAME or "MindPrism",
                "amount_inr": amount_inr,
                "txn_ref": txn_ref,
                "deep_link": deep_link,
                # Frontend instruction: show two CTAs — "Open UPI app" (mobile)
                # and "Show QR" (desktop). After payment, button "I've paid"
                # POSTs to /api/v3/payment/upi/confirm with txn_ref.
            },
        )

    def verify_payment(self, txn_id: str | None) -> bool:
        """No automated verification. Operator manually confirms via dashboard
        or via a periodic bank-statement reconciler. Returns False here so
        the polling endpoint never silently confirms — the manual confirm
        endpoint sets ``paid=True`` explicitly.
        """
        return False

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        # No webhooks for direct UPI Intent.
        return False
