from datetime import datetime, timedelta
from jose import jwt
from backend.config import settings
from backend.db.database import SessionLocal
from backend.db.models import User

db = SessionLocal()
user = db.query(User).first()
token = jwt.encode(
    {"sub": str(user.id), "exp": datetime.utcnow() + timedelta(days=60)},
    settings.secret_key,
    algorithm="HS256",
)
print("Username:", user.username)
print("Token:", token)
