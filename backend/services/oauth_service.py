"""OAuth helpers for Twitter (X) and Telegram login verification."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from urllib.parse import urlencode

import httpx

from config import settings


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def create_twitter_pkce_state() -> tuple[str, str]:
    verifier = _b64url(secrets.token_bytes(48))
    challenge = _b64url(hashlib.sha256(verifier.encode("utf-8")).digest())

    payload = {
        "verifier": verifier,
        "nonce": secrets.token_urlsafe(12),
        "exp": int(time.time()) + 600,
    }
    body = _b64url(json.dumps(payload).encode("utf-8"))
    sig = _b64url(
        hmac.new(
            settings.OAUTH_STATE_SECRET.encode("utf-8"),
            body.encode("utf-8"),
            hashlib.sha256,
        ).digest()
    )
    state = f"{body}.{sig}"
    return challenge, state


def parse_twitter_state(state: str) -> str:
    try:
        body, sig = state.split(".", 1)
    except ValueError as exc:
        raise ValueError("Invalid state") from exc

    expected_sig = _b64url(
        hmac.new(
            settings.OAUTH_STATE_SECRET.encode("utf-8"),
            body.encode("utf-8"),
            hashlib.sha256,
        ).digest()
    )
    if not hmac.compare_digest(sig, expected_sig):
        raise ValueError("Invalid state signature")

    payload = json.loads(base64.urlsafe_b64decode(body + "==").decode("utf-8"))
    if payload.get("exp", 0) < int(time.time()):
        raise ValueError("State expired")
    return payload["verifier"]


def build_twitter_authorize_url() -> str:
    if not settings.TWITTER_CLIENT_ID:
        raise ValueError("TWITTER_CLIENT_ID is not configured")
    if not settings.OAUTH_STATE_SECRET:
        raise ValueError("OAUTH_STATE_SECRET is not configured")

    challenge, state = create_twitter_pkce_state()
    params = {
        "response_type": "code",
        "client_id": settings.TWITTER_CLIENT_ID,
        "redirect_uri": settings.TWITTER_REDIRECT_URI,
        "scope": "users.read tweet.read",
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    return f"https://twitter.com/i/oauth2/authorize?{urlencode(params)}"


async def exchange_twitter_code(code: str, state: str) -> dict:
    verifier = parse_twitter_state(state)

    token_url = "https://api.twitter.com/2/oauth2/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.TWITTER_REDIRECT_URI,
        "client_id": settings.TWITTER_CLIENT_ID,
        "code_verifier": verifier,
    }

    auth = None
    if settings.TWITTER_CLIENT_SECRET:
        auth = (settings.TWITTER_CLIENT_ID, settings.TWITTER_CLIENT_SECRET)

    async with httpx.AsyncClient(timeout=20) as client:
        token_resp = await client.post(token_url, data=data, auth=auth)
        token_resp.raise_for_status()
        token_data = token_resp.json()

        access_token = token_data.get("access_token")
        if not access_token:
            raise ValueError("Twitter access_token not found")

        user_resp = await client.get(
            "https://api.twitter.com/2/users/me",
            params={"user.fields": "id,name,username,profile_image_url"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        user_resp.raise_for_status()
        user_data = user_resp.json().get("data", {})

    if not user_data.get("id"):
        raise ValueError("Twitter user id missing")

    return {
        "external_id": str(user_data["id"]),
        "handle": user_data.get("username"),
        "public": user_data,
    }


def verify_telegram_callback(payload: dict[str, str]) -> dict:
    if not settings.TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is not configured")

    incoming_hash = payload.get("hash")
    auth_date = int(payload.get("auth_date", "0"))
    if int(time.time()) - auth_date > 86400:
        raise ValueError("Telegram auth_date expired")

    data_check = []
    for key in sorted(k for k in payload.keys() if k != "hash"):
        value = payload.get(key)
        if value is not None:
            data_check.append(f"{key}={value}")
    data_check_string = "\n".join(data_check)

    secret = hashlib.sha256(settings.TELEGRAM_BOT_TOKEN.encode("utf-8")).digest()
    computed = hmac.new(secret, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

    if not incoming_hash or not hmac.compare_digest(incoming_hash, computed):
        raise ValueError("Invalid Telegram hash")

    external_id = payload.get("id")
    if not external_id:
        raise ValueError("Telegram user id missing")

    return {
        "external_id": str(external_id),
        "handle": payload.get("username"),
        "public": {
            "first_name": payload.get("first_name"),
            "last_name": payload.get("last_name"),
            "photo_url": payload.get("photo_url"),
            "auth_date": payload.get("auth_date"),
        },
    }


# ---------------------------------------------------------------------------
# Google OAuth 2.0
# ---------------------------------------------------------------------------

def build_google_authorize_url() -> str:
    if not settings.GOOGLE_CLIENT_ID:
        raise ValueError("GOOGLE_CLIENT_ID is not configured")

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "state": secrets.token_urlsafe(16),
        "prompt": "consent",
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"


async def exchange_google_code(code: str) -> dict:
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
    }

    async with httpx.AsyncClient(timeout=20) as client:
        token_resp = await client.post(token_url, data=data)
        token_resp.raise_for_status()
        access_token = token_resp.json().get("access_token")
        if not access_token:
            raise ValueError("Google access_token not found")

        user_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        user_resp.raise_for_status()
        user_data = user_resp.json()

    if not user_data.get("id"):
        raise ValueError("Google user id missing")

    return {
        "external_id": str(user_data["id"]),
        "handle": user_data.get("name"),
        "email": user_data.get("email"),
        "public": {
            "name": user_data.get("name"),
            "email": user_data.get("email"),
            "picture": user_data.get("picture"),
        },
    }


# ---------------------------------------------------------------------------
# WhatsApp (Meta / Facebook) OAuth
# ---------------------------------------------------------------------------

def build_whatsapp_authorize_url() -> str:
    if not settings.META_APP_ID:
        raise ValueError("META_APP_ID is not configured")

    params = {
        "client_id": settings.META_APP_ID,
        "redirect_uri": settings.META_REDIRECT_URI,
        "response_type": "code",
        "scope": "public_profile,email",
        "state": secrets.token_urlsafe(16),
    }
    return f"https://www.facebook.com/v19.0/dialog/oauth?{urlencode(params)}"


async def exchange_whatsapp_code(code: str) -> dict:
    token_url = "https://graph.facebook.com/v19.0/oauth/access_token"
    params = {
        "client_id": settings.META_APP_ID,
        "client_secret": settings.META_APP_SECRET,
        "redirect_uri": settings.META_REDIRECT_URI,
        "code": code,
    }

    async with httpx.AsyncClient(timeout=20) as client:
        token_resp = await client.get(token_url, params=params)
        token_resp.raise_for_status()
        access_token = token_resp.json().get("access_token")
        if not access_token:
            raise ValueError("Meta access_token not found")

        user_resp = await client.get(
            "https://graph.facebook.com/me",
            params={"fields": "id,name,email,picture", "access_token": access_token},
        )
        user_resp.raise_for_status()
        user_data = user_resp.json()

    if not user_data.get("id"):
        raise ValueError("Meta user id missing")

    return {
        "external_id": str(user_data["id"]),
        "handle": user_data.get("name"),
        "email": user_data.get("email"),
        "public": {
            "name": user_data.get("name"),
            "email": user_data.get("email"),
            "picture": user_data.get("picture", {}).get("data", {}).get("url") if isinstance(user_data.get("picture"), dict) else None,
        },
    }
