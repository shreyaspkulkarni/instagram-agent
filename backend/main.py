from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.db.database import SessionLocal, create_tables
from backend.db.models import User
from backend.api.routes import auth, captions, photos

app = FastAPI(title="Instagram AI Agent", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    create_tables()
    _ensure_default_user()


def _ensure_default_user():
    db = SessionLocal()
    try:
        if not db.query(User).first():
            user = User(instagram_id="local", username="local", access_token="none")
            db.add(user)
            db.commit()
    finally:
        db.close()


app.include_router(auth.router)
app.include_router(photos.router)
app.include_router(captions.router)


@app.get("/health")
def health():
    return {"status": "ok"}
