import secrets
from datetime import datetime, timedelta
from urllib.parse import urlencode

import httpx

from backend.config import settings

# Instagram Graph API OAuth endpoints
AUTHORIZATION_URL = "https://api.instagram.com/oauth/authorize"
TOKEN_URL = "https://api.instagram.com/oauth/access_token"
LONG_LIVED_TOKEN_URL = "https://graph.instagram.com/access_token"
GRAPH_API_BASE = "https://graph.instagram.com/v21.0"

# Read-only scopes — agent advises, user posts manually
SCOPES = [
    "instagram_business_basic",
    "instagram_business_manage_comments",
]

# State stored with expiry so it survives across reload cycles
_state_store: dict[str, datetime] = {}
_STATE_TTL_MINUTES = 10


def generate_auth_url() -> tuple[str, str]:
    state = secrets.token_urlsafe(32)
    _state_store[state] = datetime.utcnow() + timedelta(minutes=_STATE_TTL_MINUTES)
    params = {
        "client_id": settings.instagram_app_id,
        "redirect_uri": settings.instagram_redirect_uri,
        "scope": ",".join(SCOPES),
        "response_type": "code",
        "state": state,
    }
    return f"{AUTHORIZATION_URL}?{urlencode(params)}", state


def verify_state(state: str) -> bool:
    expiry = _state_store.get(state)
    if expiry and datetime.utcnow() < expiry:
        del _state_store[state]
        return True
    return False


async def exchange_code_for_token(code: str) -> dict:
    """Exchange auth code for a short-lived token, then upgrade to long-lived."""
    async with httpx.AsyncClient() as client:
        # Step 1: short-lived token (valid 1 hour)
        resp = await client.post(
            TOKEN_URL,
            data={
                "client_id": settings.instagram_app_id,
                "client_secret": settings.instagram_app_secret,
                "grant_type": "authorization_code",
                "redirect_uri": settings.instagram_redirect_uri,
                "code": code,
            },
        )
        resp.raise_for_status()
        short_lived = resp.json()

        # Step 2: long-lived token (valid 60 days)
        resp2 = await client.get(
            LONG_LIVED_TOKEN_URL,
            params={
                "grant_type": "ig_exchange_token",
                "client_secret": settings.instagram_app_secret,
                "access_token": short_lived["access_token"],
            },
        )
        resp2.raise_for_status()
        return resp2.json()  # {"access_token": ..., "token_type": ..., "expires_in": ...}


async def get_instagram_profile(access_token: str) -> dict:
    """Fetch basic profile data for the authenticated user."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{GRAPH_API_BASE}/me",
            params={
                "fields": "id,username,name,profile_picture_url,biography,followers_count,follows_count,media_count",
                "access_token": access_token,
            },
        )
        resp.raise_for_status()
        return resp.json()
