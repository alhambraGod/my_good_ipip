"""Application settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_ENV: str = "dev"  # "dev", "stage", or "prod"
    LOG_ROOT: str = "/var/MindPrism"           # base dir for centralised logs
    LOG_FALLBACK_ROOT: str = "./logs"          # used when LOG_ROOT is unwritable
    LOG_RETENTION_DAYS: int = 30
    DATABASE_URL: str = "sqlite:///./mindiq.db"
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    OPENAI_API_KEY: str = ""
    PAYMENT_MODE: str = "mock"  # "stripe" or "mock"
    FRONTEND_URL: str = "http://localhost:3000"
    # Public base URL for API (short links /s/{code}, webhooks). Defaults to local backend.
    API_PUBLIC_URL: str = "http://localhost:3001"
    REPORT_PRICE_CENTS: int = 399  # $3.99
    REPORT_CURRENCY: str = "usd"

    SOCIAL_MODE: str = "manual"  # "manual" or "oauth"
    X_BEARER_TOKEN: str = ""
    PERSONALIZATION_VERSION: str = "local_v1"
    QUESTION_BANK_VERSION: str = "v2_100"

    TWITTER_CLIENT_ID: str = ""
    TWITTER_CLIENT_SECRET: str = ""
    TWITTER_REDIRECT_URI: str = "http://localhost:3000/auth/twitter/callback"
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_BOT_USERNAME: str = ""
    OAUTH_STATE_SECRET: str = ""

    DEV_ACCOUNT_ENABLED: bool = False
    DEV_ACCOUNT_EMAIL: str = "dev@dev"
    DEV_ACCOUNT_PASSWORD: str = "dev@dev"

    JWT_SECRET: str = "change_me_jwt_secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_DAYS: int = 30

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:3000/auth/google/callback"

    META_APP_ID: str = ""
    META_APP_SECRET: str = ""
    META_REDIRECT_URI: str = "http://localhost:3000/auth/whatsapp/callback"

    FACEBOOK_APP_ID: str = ""
    FACEBOOK_APP_SECRET: str = ""

    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""

    # ── Payment provider registry ──────────────────────────────────────
    # See docs/PAYMENT_PROVIDERS.md for the full landscape. PAYMENT_MODE
    # is kept for back-compat (it picks the single default driver).
    PAYMENT_DEFAULT_DRIVER: str = ""           # explicit override; if empty, falls back to PAYMENT_MODE
    PAYMENT_DRIVERS_ENABLED: str = ""          # comma list, e.g. "razorpay,upi,cashfree,mock"

    # Cashfree
    CASHFREE_CLIENT_ID: str = ""
    CASHFREE_CLIENT_SECRET: str = ""
    CASHFREE_WEBHOOK_SECRET: str = ""
    CASHFREE_API_BASE: str = "https://sandbox.cashfree.com"

    # PayU India
    PAYU_MERCHANT_KEY: str = ""
    PAYU_MERCHANT_SALT: str = ""
    PAYU_API_BASE: str = "https://test.payu.in"

    # Direct UPI Intent (no aggregator)
    UPI_VPA: str = ""                          # e.g. "mindprism@hdfcbank"
    UPI_DISPLAY_NAME: str = "MindPrism"

    # ── dev/prod paywall gating ────────────────────────────────────────
    # When True, GET /api/v3/report/{id} returns the deep report even if
    # the assessment is unpaid (with `is_preview: true` so the UI watermarks).
    # Default: True in dev, False in prod (computed below in __init__-style).
    ALLOW_FREE_REPORT: bool = False            # overridden per-env in `_finalize()`

    PROMO_MAX_REDEMPTIONS: int = 1000
    PRICE_FULL_INR: int = 99
    PRICE_PROMO_INR: int = 49

    @property
    def is_dev(self) -> bool:
        return self.APP_ENV in ("dev", "test")

    @property
    def is_prod(self) -> bool:
        return self.APP_ENV == "prod"

    class Config:
        env_file = ".env"


def _finalize_settings(s: "Settings") -> "Settings":
    """Apply env-aware defaults the dataclass can't express directly."""
    # ALLOW_FREE_REPORT default: True in dev/test, False in prod/stage.
    # If the env var is explicitly set, BaseSettings already applied it.
    import os
    if os.environ.get("ALLOW_FREE_REPORT") is None:
        s.ALLOW_FREE_REPORT = s.is_dev
    return s


settings = _finalize_settings(Settings())
