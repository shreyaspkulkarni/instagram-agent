import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from backend.db.database import Base

EMBEDDING_DIM = 3072  # gemini-embedding-001


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instagram_id = Column(String, unique=True, nullable=False)
    username = Column(String, nullable=False)
    name = Column(String, default="")
    profile_picture = Column(String, default="")
    access_token = Column(Text, nullable=False)
    token_expiry = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    memory = relationship("UserMemory", back_populates="user", cascade="all, delete")
    photos = relationship("Photo", back_populates="user", cascade="all, delete")
    posts = relationship("Post", back_populates="user", cascade="all, delete")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete")
    instagram_profile = relationship("InstagramProfile", back_populates="user", uselist=False, cascade="all, delete")


class UserMemory(Base):
    __tablename__ = "user_memory"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    key = Column(String, nullable=False)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="memory")


class InstagramProfile(Base):
    __tablename__ = "instagram_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    bio = Column(Text, default="")
    followers_count = Column(Integer, default=0)
    following_count = Column(Integer, default=0)
    media_count = Column(Integer, default=0)
    avg_likes = Column(Float, default=0.0)
    avg_comments = Column(Float, default=0.0)
    best_posting_times = Column(JSONB, default=list)
    niche_tags = Column(JSONB, default=list)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="instagram_profile")


class Photo(Base):
    """A photo uploaded by the user for scoring. Originals stay on user's machine — we store metadata only."""
    __tablename__ = "photos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    original_filename = Column(String, nullable=False)

    # Vision scoring results (from Gemini 2.0 Flash via Instructor)
    score = Column(Float)                          # 0–10 overall Instagram score
    composition_notes = Column(Text)
    lighting_notes = Column(Text)
    subject_notes = Column(Text)
    niche_fit = Column(Text)
    edit_suggestions = Column(JSONB)               # list[str] human-readable
    edit_params = Column(JSONB)                    # EditParams dict — consumed by Pillow
    recommended_format = Column(String)            # square_1_1 | portrait_4_5 | landscape_16_9
    post_worthy = Column(Boolean)

    status = Column(
        Enum("scored", "approved", "rejected", name="photo_status"),
        default="scored",
    )
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="photos")
    post = relationship("Post", back_populates="photo", uselist=False)


class Post(Base):
    """A caption draft for an approved photo. User posts manually to Instagram."""
    __tablename__ = "posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    photo_id = Column(UUID(as_uuid=True), ForeignKey("photos.id"), nullable=True)
    caption = Column(Text, default="")
    hashtags = Column(Text, default="")
    status = Column(Enum("draft", "posted", name="post_status"), default="draft")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="posts")
    photo = relationship("Photo", back_populates="post")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role = Column(Enum("user", "assistant", name="conv_role"), nullable=False)
    content = Column(Text, nullable=False)
    tool_calls = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="conversations")


class CaptionExample(Base):
    """High-engagement scraped posts used for RAG caption generation."""
    __tablename__ = "caption_examples"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account = Column(String, nullable=False)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    engagement_tier = Column(String)
    caption = Column(Text, nullable=False)
    hashtags = Column(JSONB, default=list)
    embed_text = Column(Text)
    embedding = Column(Vector(EMBEDDING_DIM))
    created_at = Column(DateTime, default=datetime.utcnow)
