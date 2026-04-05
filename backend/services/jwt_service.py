"""JWT token creation and verification."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models import UserProfile

_bearer = HTTPBearer(auto_error=False)


def create_token(profile: UserProfile) -> str:
    """Create a JWT for the given user profile."""
    payload = {
        "sub": profile.id,
        "st": profile.session_token,
        "exp": datetime.now(timezone.utc) + timedelta(days=settings.JWT_EXPIRY_DAYS),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and verify a JWT. Raises HTTPException on failure."""
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    token: str | None = Query(None, alias="token"),
    db: Session = Depends(get_db),
) -> UserProfile:
    """FastAPI dependency: extract user from Bearer header or ?token= query param."""
    raw_token = None
    if credentials:
        raw_token = credentials.credentials
    elif token:
        raw_token = token

    if not raw_token:
        raise HTTPException(status_code=401, detail="Authentication required")

    payload = decode_token(raw_token)
    profile = db.query(UserProfile).filter(UserProfile.id == payload.get("sub")).first()
    if not profile:
        raise HTTPException(status_code=401, detail="User not found")
    return profile


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    token: str | None = Query(None, alias="token"),
    db: Session = Depends(get_db),
) -> UserProfile | None:
    """Same as get_current_user but returns None instead of raising."""
    raw_token = None
    if credentials:
        raw_token = credentials.credentials
    elif token:
        raw_token = token

    if not raw_token:
        return None

    try:
        payload = decode_token(raw_token)
    except HTTPException:
        return None

    return db.query(UserProfile).filter(UserProfile.id == payload.get("sub")).first()
