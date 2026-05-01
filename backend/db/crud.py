from datetime import datetime

from sqlalchemy.orm import Session

from backend.db.models import Conversation, InstagramProfile, Post, User, UserMemory


def create_or_update_user(
    db: Session,
    instagram_id: str,
    username: str,
    name: str,
    profile_picture: str,
    access_token: str,
    token_expiry: datetime | None = None,
) -> User:
    user = db.query(User).filter(User.instagram_id == instagram_id).first()
    if user:
        user.username = username
        user.name = name
        user.profile_picture = profile_picture
        user.access_token = access_token
        if token_expiry:
            user.token_expiry = token_expiry
    else:
        user = User(
            instagram_id=instagram_id,
            username=username,
            name=name,
            profile_picture=profile_picture,
            access_token=access_token,
            token_expiry=token_expiry,
        )
        db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_id(db: Session, user_id: str) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def save_memory(db: Session, user_id: str, key: str, value: str) -> UserMemory:
    mem = db.query(UserMemory).filter(UserMemory.user_id == user_id, UserMemory.key == key).first()
    if mem:
        mem.value = value
        mem.updated_at = datetime.utcnow()
    else:
        mem = UserMemory(user_id=user_id, key=key, value=value)
        db.add(mem)
    db.commit()
    db.refresh(mem)
    return mem


def get_memory(db: Session, user_id: str) -> dict:
    entries = db.query(UserMemory).filter(UserMemory.user_id == user_id).all()
    return {e.key: e.value for e in entries}


def save_conversation(db: Session, user_id: str, role: str, content: str, tool_calls=None) -> Conversation:
    conv = Conversation(user_id=user_id, role=role, content=content, tool_calls=tool_calls)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def get_conversation_history(db: Session, user_id: str, limit: int = 20) -> list[Conversation]:
    return (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(Conversation.created_at.desc())
        .limit(limit)
        .all()
    )


def upsert_instagram_profile(db: Session, user_id: str, **kwargs) -> InstagramProfile:
    profile = db.query(InstagramProfile).filter(InstagramProfile.user_id == user_id).first()
    if profile:
        for k, v in kwargs.items():
            setattr(profile, k, v)
        profile.updated_at = datetime.utcnow()
    else:
        profile = InstagramProfile(user_id=user_id, **kwargs)
        db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile
