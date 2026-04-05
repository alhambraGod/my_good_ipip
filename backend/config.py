"""Application settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_ENV: str = "dev"  # "dev", "stage", or "prod"
    DATABASE_URL: str = "sqlite:///./mindiq.db"
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    OPENAI_API_KEY: str = ""
    PAYMENT_MODE: str = "mock"  # "stripe" or "mock"
    FRONTEND_URL: str = "http://localhost:3000"
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

    @property
    def is_dev(self) -> bool:
        return self.APP_ENV == "dev"

    @property
    def is_prod(self) -> bool:
        return self.APP_ENV == "prod"

    class Config:
        env_file = ".env"


settings = Settings()
