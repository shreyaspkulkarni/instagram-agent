from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.db.models import User


def get_default_user_id(db: Session) -> str:
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=500, detail="No user found. Server not initialized.")
    return str(user.id)
