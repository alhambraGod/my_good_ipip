"""Multi-provider payment driver registry.

Drivers are instantiated lazily so an unset Razorpay credential doesn't
prevent the Mock driver from working in dev.

Operator configuration:
    PAYMENT_MODE                   default driver id (back-compat single name)
    PAYMENT_DEFAULT_DRIVER         (preferred) explicit default id
    PAYMENT_DRIVERS_ENABLED        comma-list of enabled driver ids
                                   e.g. "razorpay,upi,cashfree,mock"

If `PAYMENT_DRIVERS_ENABLED` is empty, we fall back to a single-driver
deployment (whatever `PAYMENT_MODE` / `PAYMENT_DEFAULT_DRIVER` says),
preserving the v1 behaviour.
"""

from __future__ import annotations

from typing import Callable

import config  # late-binding: importlib.reload(config) in tests must take effect.
from services.payment.base import PaymentDriver, PaymentProvider, ProviderInfo
from services.payment.cashfree_driver import CashfreeDriver
from services.payment.mock import MockDriver
from services.payment.payu_driver import PayUDriver
from services.payment.razorpay_driver import RazorpayDriver
from services.payment.upi_intent_driver import UPIIntentDriver


# Each entry: id → factory. We keep them as zero-arg callables so an
# unconfigured driver doesn't blow up at import time.
DRIVER_FACTORIES: dict[PaymentProvider, Callable[[], PaymentDriver]] = {
    "mock":     MockDriver,
    "razorpay": RazorpayDriver,
    "cashfree": CashfreeDriver,
    "payu":     PayUDriver,
    "upi":      UPIIntentDriver,
}


def _enabled_ids() -> list[PaymentProvider]:
    """Resolve the list of enabled driver ids from settings.

    Order:
      1. `PAYMENT_DRIVERS_ENABLED` (comma list) if set.
      2. Otherwise just [default_driver()] for back-compat.
    """
    raw = (config.settings.PAYMENT_DRIVERS_ENABLED or "").strip()
    if raw:
        ids = [s.strip().lower() for s in raw.split(",") if s.strip()]
        return [i for i in ids if i in DRIVER_FACTORIES]  # type: ignore[misc]
    return [default_driver_id()]


def default_driver_id() -> PaymentProvider:
    """Pick the default driver for a single-payment-method UI."""
    explicit = (config.settings.PAYMENT_DEFAULT_DRIVER or "").strip().lower()
    if explicit and explicit in DRIVER_FACTORIES:
        return explicit  # type: ignore[return-value]
    mode = (config.settings.PAYMENT_MODE or "mock").strip().lower()
    if mode in DRIVER_FACTORIES:
        return mode  # type: ignore[return-value]
    return "mock"


def get_payment_driver(name: str | None = None) -> PaymentDriver:
    """Instantiate a driver by id (default = `default_driver_id()`).

    Raises:
      ValueError if the id isn't enabled or isn't registered.
    """
    chosen = (name or default_driver_id()).strip().lower()
    if chosen not in DRIVER_FACTORIES:
        raise ValueError(
            f"Unknown payment driver: {chosen!r}; "
            f"registered: {sorted(DRIVER_FACTORIES)}"
        )
    if chosen not in _enabled_ids():
        raise ValueError(
            f"Payment driver {chosen!r} is not enabled in PAYMENT_DRIVERS_ENABLED "
            f"(currently: {settings.PAYMENT_DRIVERS_ENABLED!r})"
        )
    return DRIVER_FACTORIES[chosen]()  # type: ignore[index]


def list_provider_infos() -> list[ProviderInfo]:
    """Return the public ProviderInfo for every enabled driver.

    Drivers that fail to instantiate (missing creds, etc.) are omitted —
    the operator can re-enable them by adding the missing env vars.
    """
    out: list[ProviderInfo] = []
    default = default_driver_id()
    for pid in _enabled_ids():
        factory = DRIVER_FACTORIES.get(pid)
        if not factory:
            continue
        try:
            inst = factory()
        except Exception:
            # Can't instantiate (e.g. missing creds). Skip — not enabled.
            continue
        info = inst.info
        if pid == default:
            info = ProviderInfo(
                id=info.id,
                label_en=info.label_en,
                label_hi=info.label_hi,
                description_en=info.description_en,
                supports_methods=info.supports_methods,
                requires_redirect=info.requires_redirect,
                recommended=True,
                enabled=info.enabled,
            )
        out.append(info)
    return out
