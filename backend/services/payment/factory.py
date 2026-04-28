"""Payment driver selector keyed off PAYMENT_MODE setting."""

from __future__ import annotations

from config import settings
from services.payment.base import PaymentDriver
from services.payment.mock import MockDriver
from services.payment.razorpay_driver import RazorpayDriver


def get_payment_driver() -> PaymentDriver:
    """Return the configured payment driver.

    Modes:
      - mock      → MockDriver (dev / test)
      - razorpay  → RazorpayDriver (India production)
      - wechat    → WeChatDriver (TBD; not yet implemented)
      - stripe    → legacy services.payment_service path (kept for non-India)
    """
    mode = settings.PAYMENT_MODE
    if mode == "mock":
        return MockDriver()
    if mode == "razorpay":
        return RazorpayDriver()
    raise ValueError(f"Unsupported PAYMENT_MODE: {mode!r}; supported: mock, razorpay")
