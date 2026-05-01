from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from jose import jwt
from sqlalchemy.orm import Session

from backend.config import settings
from backend.db.crud import create_or_update_user
from backend.db.database import get_db
from backend.instagram.auth import exchange_code_for_token, generate_auth_url, get_instagram_profile, verify_state

router = APIRouter(prefix="/auth", tags=["auth"])

ALGORITHM = "HS256"
TOKEN_EXPIRE_DAYS = 60


def create_jwt(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(days=TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


@router.get("/instagram/login")
async def login():
    auth_url, _ = generate_auth_url()
    return RedirectResponse(url=auth_url)


@router.get("/instagram/callback")
async def callback(code: str, state: str, db: Session = Depends(get_db)):
    if not verify_state(state):
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    token_data = await exchange_code_for_token(code)
    access_token = token_data["access_token"]
    expires_in = token_data.get("expires_in", 60 * 24 * 3600)
    token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)

    profile = await get_instagram_profile(access_token)

    user = create_or_update_user(
        db=db,
        instagram_id=profile["id"],
        username=profile.get("username", ""),
        name=profile.get("name", ""),
        profile_picture=profile.get("profile_picture_url", ""),
        access_token=access_token,
        token_expiry=token_expiry,
    )

    jwt_token = create_jwt(str(user.id))
    return RedirectResponse(url=f"{settings.frontend_url}/auth/callback?token={jwt_token}")


@router.get("/me")
async def get_me(db: Session = Depends(get_db)):
    """Health check — returns a reminder to use JWT auth (wired in Phase 3)."""
    return {"message": "Use Authorization: Bearer <token> header"}
