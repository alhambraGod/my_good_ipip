"""PayU India payment driver — form POST flow + SHA-512 hash.

Reference: https://payu.in/docs

PayU's classic flow expects the merchant to compute a SHA-512 hash, send
the user's browser to PayU as an HTML form POST, and verify the same
hash on the redirect-back URL. There's no "in-page modal" mode.

This driver returns enough info for the frontend to build the form
(or you can just call `build_form_html()` server-side and dump the HTML
to the browser; both flows are wired in the v3 router).
"""

from __future__ import annotations

import hashlib

import httpx

import config
from services.payment.base import PaymentIntent, ProviderInfo


class PayUDriver:
    """PayU Money / PayU Biz redirect-flow driver."""

    provider_name = "payu"

    @property
    def info(self) -> ProviderInfo:
        return ProviderInfo(
            id="payu",
            label_en="UPI / Card (PayU)",
            label_hi="UPI / Card (PayU)",
            description_en="Redirect-style checkout via PayU. Use as fallback if Razorpay is down.",
            supports_methods=("UPI", "Card", "NetBanking", "Wallet", "EMI"),
            requires_redirect=True,
            recommended=False,
            enabled=True,
        )

    def __init__(self) -> None:
        s = config.settings
        if not s.PAYU_MERCHANT_KEY or not s.PAYU_MERCHANT_SALT:
            raise ValueError(
                "PAYU_MERCHANT_KEY + PAYU_MERCHANT_SALT must be set "
                "(see env/<env>.env)"
            )

    def _api_base(self) -> str:
        return config.settings.PAYU_API_BASE.rstrip("/")

    def _hash_request(
        self,
        *,
        txnid: str,
        amount: str,
        productinfo: str,
        firstname: str,
        email: str,
    ) -> str:
        s = config.settings
        # PayU request hash:
        # sha512(key|txnid|amount|productinfo|firstname|email|||||||||||salt)
        raw = (
            f"{s.PAYU_MERCHANT_KEY}|{txnid}|{amount}|{productinfo}|{firstname}|{email}"
            "|||||||||||"
            f"{s.PAYU_MERCHANT_SALT}"
        )
        return hashlib.sha512(raw.encode()).hexdigest()

    def hash_response(
        self,
        *,
        txnid: str,
        amount: str,
        productinfo: str,
        firstname: str,
        email: str,
        status: str,
    ) -> str:
        """Compute PayU's response hash (used to verify the success/cancel callback).

        Spec: sha512(salt|status||||||||||email|firstname|productinfo|amount|txnid|key)
        """
        s = config.settings
        raw = (
            f"{s.PAYU_MERCHANT_SALT}|{status}||||||||||"
            f"{email}|{firstname}|{productinfo}|{amount}|{txnid}|{s.PAYU_MERCHANT_KEY}"
        )
        return hashlib.sha512(raw.encode()).hexdigest()

    def create_payment_intent(self, assessment_id: str, amount_inr: int) -> PaymentIntent:
        s = config.settings
        txnid = f"mpz_{assessment_id[:24]}"
        amount = f"{amount_inr:.2f}"
        productinfo = "MindPrism Report"
        firstname = "User"
        email = "user@mindprism.in"
        h = self._hash_request(
            txnid=txnid, amount=amount,
            productinfo=productinfo, firstname=firstname, email=email,
        )
        # Build the form fields the frontend will POST to PayU's _payment endpoint.
        post_url = f"{self._api_base()}/_payment"
        fields: dict[str, str] = {
            "key": s.PAYU_MERCHANT_KEY,
            "txnid": txnid,
            "amount": amount,
            "productinfo": productinfo,
            "firstname": firstname,
            "email": email,
            "phone": "9999999999",
            "surl": f"{s.FRONTEND_URL}/payment/success?assessment_id={assessment_id}&provider=payu",
            "furl": f"{s.FRONTEND_URL}/payment/success?assessment_id={assessment_id}&provider=payu&status=fail",
            "hash": h,
            "udf1": assessment_id,
        }
        return PaymentIntent(
            provider="payu",
            assessment_id=assessment_id,
            amount_inr=amount_inr,
            txn_id=txnid,
            payment_url=post_url,
            client_payload={
                "method": "POST",
                "form_url": post_url,
                "fields": fields,
            },
        )

    def verify_payment(self, txn_id: str | None) -> bool:
        """Verify a transaction via PayU's verify_payment API.

        PayU exposes ``/merchant/postservice.php?form=2`` which accepts
        ``key + command=verify_payment + var1=txnid + hash``.
        Hash spec: sha512(key|command|var1|salt).
        """
        if not txn_id:
            return False
        s = config.settings
        command = "verify_payment"
        raw = f"{s.PAYU_MERCHANT_KEY}|{command}|{txn_id}|{s.PAYU_MERCHANT_SALT}"
        h = hashlib.sha512(raw.encode()).hexdigest()
        with httpx.Client(timeout=15.0) as client:
            r = client.post(
                f"{self._api_base()}/merchant/postservice.php?form=2",
                data={
                    "key": s.PAYU_MERCHANT_KEY,
                    "command": command,
                    "var1": txn_id,
                    "hash": h,
                },
            )
            if r.status_code != 200:
                return False
            data = r.json()
        try:
            return data["transaction_details"][txn_id]["status"] == "success"
        except (KeyError, TypeError):
            return False

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """PayU 'webhook' is the redirect-back POST. The frontend already
        verifies via ``hash_response``; this method exists for protocol
        completeness and just re-verifies the hash sent in the body.

        Body format: ``txnid=...&amount=...&...&hash=...`` (form-encoded).
        """
        try:
            from urllib.parse import parse_qs
            q = {k: v[0] for k, v in parse_qs(payload.decode("utf-8")).items()}
            return q.get("hash") == self.hash_response(
                txnid=q.get("txnid", ""),
                amount=q.get("amount", ""),
                productinfo=q.get("productinfo", ""),
                firstname=q.get("firstname", ""),
                email=q.get("email", ""),
                status=q.get("status", ""),
            )
        except Exception:
            return False
