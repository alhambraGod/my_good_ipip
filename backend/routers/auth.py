"""Authentication router — email, Google, WhatsApp, Twitter, Telegram, dev login."""

from __future__ import annotations

import uuid

import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models import UserProfile
from schemas import (
    AuthResponse,
    DevLoginRequest,
    EmailLoginRequest,
    EmailRegisterRequest,
    OAuthFinishRequest,
    OAuthStartResponse,
    TelegramCallbackRequest,
)
from services.jwt_service import create_token
from services.oauth_service import (
    build_google_authorize_url,
    build_twitter_authorize_url,
    build_whatsapp_authorize_url,
    exchange_google_code,
    exchange_twitter_code,
    exchange_whatsapp_code,
    verify_telegram_callback,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _upsert_profile(
    provider: str,
    external_id: str,
    handle: str | None,
    public_data: dict,
    db: Session,
    email: str | None = None,
) -> UserProfile:
    profile = (
        db.query(UserProfile)
        .filter(UserProfile.provider == provider, UserProfile.external_id == external_id)
        .first()
    )

    if profile:
        profile.external_handle = handle
        profile.external_public_data = public_data
        if email and not profile.email:
            profile.email = email
        db.commit()
        db.refresh(profile)
        return profile

    profile = UserProfile(
        session_token=str(uuid.uuid4()),
        provider=provider,
        external_id=external_id,
        external_handle=handle,
        external_public_data=public_data,
        email=email,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def _auth_response(profile: UserProfile, provider: str) -> AuthResponse:
    return AuthResponse(
        access_token=create_token(profile),
        provider=provider,
        handle=profile.external_handle or profile.display_name,
        session_token=profile.session_token,
    )


# ---------------------------------------------------------------------------
# Email register / login
# ---------------------------------------------------------------------------

@router.post("/register", response_model=AuthResponse)
def email_register(payload: EmailRegisterRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email")
    if len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    existing = db.query(UserProfile).filter(UserProfile.email == email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    pw_hash = bcrypt.hashpw(payload.password.encode(), bcrypt.gensalt()).decode()

    profile = UserProfile(
        session_token=str(uuid.uuid4()),
        provider="email",
        external_id=email,
        email=email,
        password_hash=pw_hash,
        display_name=payload.name,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    return _auth_response(profile, "email")


@router.post("/login", response_model=AuthResponse)
def email_login(payload: EmailLoginRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    profile = db.query(UserProfile).filter(UserProfile.email == email).first()
    if not profile or not profile.password_hash:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not bcrypt.checkpw(payload.password.encode(), profile.password_hash.encode()):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return _auth_response(profile, profile.provider)


# ---------------------------------------------------------------------------
# Google OAuth
# ---------------------------------------------------------------------------

@router.get("/google/start", response_model=OAuthStartResponse)
def google_start():
    try:
        auth_url = build_google_authorize_url()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return OAuthStartResponse(auth_url=auth_url)


@router.post("/google/callback", response_model=AuthResponse)
async def google_callback(payload: OAuthFinishRequest, db: Session = Depends(get_db)):
    try:
        identity = await exchange_google_code(payload.code)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Google OAuth failed: {exc}") from exc

    profile = _upsert_profile(
        provider="google",
        external_id=identity["external_id"],
        handle=identity.get("handle"),
        public_data=identity.get("public", {}),
        db=db,
        email=identity.get("email"),
    )

    return _auth_response(profile, "google")


# ---------------------------------------------------------------------------
# WhatsApp (Meta) OAuth
# ---------------------------------------------------------------------------

@router.get("/whatsapp/start", response_model=OAuthStartResponse)
def whatsapp_start():
    try:
        auth_url = build_whatsapp_authorize_url()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return OAuthStartResponse(auth_url=auth_url)


@router.post("/whatsapp/callback", response_model=AuthResponse)
async def whatsapp_callback(payload: OAuthFinishRequest, db: Session = Depends(get_db)):
    try:
        identity = await exchange_whatsapp_code(payload.code)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"WhatsApp OAuth failed: {exc}") from exc

    profile = _upsert_profile(
        provider="whatsapp",
        external_id=identity["external_id"],
        handle=identity.get("handle"),
        public_data=identity.get("public", {}),
        db=db,
        email=identity.get("email"),
    )

    return _auth_response(profile, "whatsapp")


# ---------------------------------------------------------------------------
# Twitter (X) OAuth
# ---------------------------------------------------------------------------

@router.get("/twitter/start", response_model=OAuthStartResponse)
def twitter_start():
    try:
        auth_url = build_twitter_authorize_url()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return OAuthStartResponse(auth_url=auth_url)


@router.post("/twitter/callback", response_model=AuthResponse)
async def twitter_callback(payload: OAuthFinishRequest, db: Session = Depends(get_db)):
    try:
        identity = await exchange_twitter_code(payload.code, payload.state)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Twitter OAuth failed: {exc}") from exc

    profile = _upsert_profile(
        provider="x",
        external_id=identity["external_id"],
        handle=identity.get("handle"),
        public_data=identity.get("public", {}),
        db=db,
    )

    return _auth_response(profile, "x")


# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------

@router.post("/telegram/callback", response_model=AuthResponse)
def telegram_callback(payload: TelegramCallbackRequest, db: Session = Depends(get_db)):
    try:
        identity = verify_telegram_callback(payload.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Telegram auth failed: {exc}") from exc

    profile = _upsert_profile(
        provider="telegram",
        external_id=identity["external_id"],
        handle=identity.get("handle"),
        public_data=identity.get("public", {}),
        db=db,
    )

    return _auth_response(profile, "telegram")


# ---------------------------------------------------------------------------
# Dev tester login
# ---------------------------------------------------------------------------

@router.post("/dev-login", response_model=AuthResponse)
def dev_login(payload: DevLoginRequest, db: Session = Depends(get_db)):
    if not settings.DEV_ACCOUNT_ENABLED:
        raise HTTPException(status_code=404, detail="Not found")

    if payload.email != settings.DEV_ACCOUNT_EMAIL or payload.password != settings.DEV_ACCOUNT_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid dev credentials")

    profile = (
        db.query(UserProfile)
        .filter(UserProfile.is_dev_account.is_(True), UserProfile.provider == "manual")
        .first()
    )

    if not profile:
        profile = UserProfile(
            session_token=str(uuid.uuid4()),
            provider="manual",
            external_id="dev-account",
            external_handle="dev",
            is_dev_account=True,
            external_public_data={"email": settings.DEV_ACCOUNT_EMAIL},
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

    return _auth_response(profile, "manual")
