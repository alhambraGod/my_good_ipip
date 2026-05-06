#!/usr/bin/env python
"""Razorpay sandbox smoke test.

Walks through the full Order + Checkout-SDK signature lifecycle against
Razorpay's *test* environment, **without** touching the local FastAPI app
or DB. Use this to verify that:

  1. RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET are valid sandbox credentials
  2. Order creation works (returns order_id + amount)
  3. Our HMAC verification matches Razorpay's signing rule

This script does NOT capture a real payment — that requires the front-end
Checkout SDK driving a test card. To exercise that path, run the dev
servers (``bash start_all.sh dev``) and use the Razorpay test cards listed
at https://razorpay.com/docs/payments/payments/test-card-details/.

Usage:
    PAYMENT_MODE=razorpay \\
    RAZORPAY_KEY_ID=rzp_test_xxx \\
    RAZORPAY_KEY_SECRET=xxxxx \\
    python -m scripts.razorpay_sandbox_smoke

Env:
    RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET (required)
    RZP_SMOKE_AMOUNT_INR     default: 49
    RZP_SMOKE_ASSESSMENT_ID  default: smoke-<timestamp>
"""

from __future__ import annotations

import hashlib
import hmac
import os
import sys
import time
from pathlib import Path

# Ensure backend root is importable when invoked as `python -m scripts...`
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))


def _green(s: str) -> str:
    return f"\033[32m{s}\033[0m"


def _red(s: str) -> str:
    return f"\033[31m{s}\033[0m"


def _yellow(s: str) -> str:
    return f"\033[33m{s}\033[0m"


def main() -> int:
    key_id = os.environ.get("RAZORPAY_KEY_ID", "").strip()
    key_secret = os.environ.get("RAZORPAY_KEY_SECRET", "").strip()
    if not key_id or not key_secret:
        print(_red("ERROR: RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET must be set."))
        print(_yellow("  Hint: Razorpay Dashboard → Settings → API Keys → Generate Test Key"))
        return 2

    if not key_id.startswith("rzp_test_"):
        print(_yellow(
            f"WARNING: RAZORPAY_KEY_ID does not start with 'rzp_test_' "
            f"(got '{key_id[:12]}...') — refusing to charge a live key."
        ))
        return 2

    # Force PAYMENT_MODE=razorpay so config.settings honours the sandbox creds.
    os.environ["PAYMENT_MODE"] = "razorpay"

    # Lazy-import so the env var is in place before pydantic-settings reads it.
    import config  # noqa: WPS433
    import importlib

    importlib.reload(config)

    from services.payment.razorpay_driver import RazorpayDriver

    amount_inr = int(os.environ.get("RZP_SMOKE_AMOUNT_INR", "49"))
    assessment_id = os.environ.get(
        "RZP_SMOKE_ASSESSMENT_ID", f"smoke-{int(time.time())}"
    )

    print(_green("➜ Razorpay sandbox smoke"))
    print(f"  key id:        {key_id}")
    print(f"  amount (INR):  {amount_inr}")
    print(f"  assessment_id: {assessment_id}")

    driver = RazorpayDriver()

    print()
    print(_green("[1/3] Creating sandbox Order…"))
    try:
        order = driver.create_order(assessment_id, amount_inr=amount_inr)
    except Exception as exc:
        print(_red(f"  FAIL: create_order raised: {exc}"))
        return 3

    print(f"  order_id:     {order.order_id}")
    print(f"  amount_paise: {order.amount_paise}")
    print(f"  currency:     {order.currency}")
    if order.amount_paise != amount_inr * 100:
        print(_red(
            f"  FAIL: amount mismatch (expected {amount_inr * 100} paise, got {order.amount_paise})"
        ))
        return 3
    print(_green("  ok"))

    print()
    print(_green("[2/3] Verifying that the HMAC signing rule round-trips…"))
    fake_payment_id = "pay_smoke_local_only"
    body = f"{order.order_id}|{fake_payment_id}".encode()
    expected_sig = hmac.new(key_secret.encode(), body, hashlib.sha256).hexdigest()
    if not driver.verify_checkout_signature(
        razorpay_order_id=order.order_id,
        razorpay_payment_id=fake_payment_id,
        razorpay_signature=expected_sig,
    ):
        print(_red("  FAIL: driver rejected a signature it should have accepted"))
        return 3
    if driver.verify_checkout_signature(
        razorpay_order_id=order.order_id,
        razorpay_payment_id=fake_payment_id,
        razorpay_signature="deadbeef" + expected_sig[8:],
    ):
        print(_red("  FAIL: driver accepted a tampered signature"))
        return 3
    print(_green("  ok"))

    print()
    print(_green("[3/3] Sanity-check webhook signature helper…"))
    sample_body = b'{"event":"order.paid"}'
    webhook_secret = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "")
    if webhook_secret:
        sig = hmac.new(webhook_secret.encode(), sample_body, hashlib.sha256).hexdigest()
        if not driver.verify_webhook_signature(sample_body, sig):
            print(_red("  FAIL: webhook signature self-check did not match"))
            return 3
        print(_green("  ok"))
    else:
        print(_yellow("  skip — RAZORPAY_WEBHOOK_SECRET not set"))

    print()
    print(_green("Smoke passed. To finish a real card flow:"))
    print("  1. Start the app:    bash start_all.sh dev")
    print("  2. Take the test, click 'Unlock' on /results/<id>")
    print("  3. Use Razorpay test card: 4111 1111 1111 1111, any CVV/expiry")
    print("  4. Watch FastAPI logs for /razorpay/verify and /webhook/razorpay")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
