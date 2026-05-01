"""
One-time RAG ingestion — reads scraped posts, embeds with Google text-embedding-004,
stores in pgvector. Run after scrape_instagram.py.
"""
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# Add project root to path so we can import backend
sys.path.insert(0, str(Path(__file__).parent.parent))

from google import genai
from sqlalchemy import Column, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Session

from backend.db.database import Base, SessionLocal, engine
from pgvector.sqlalchemy import Vector
import uuid
from datetime import datetime

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
INPUT = Path("data/instagram_examples_raw.json")
EMBED_MODEL = "models/gemini-embedding-001"
VECTOR_DIM = 3072


# --- DB model for caption examples ---

class CaptionExample(Base):
    __tablename__ = "caption_examples"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account = Column(String, nullable=False)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    engagement_tier = Column(String)          # VIRAL / HIGH / SOLID
    caption = Column(Text, nullable=False)
    hashtags = Column(JSONB, default=list)
    embed_text = Column(Text)                 # text that was embedded
    embedding = Column(Vector(VECTOR_DIM))
    created_at = Column(DateTime, default=datetime.utcnow)


def embed_text(client: genai.Client, text: str) -> list[float]:
    result = client.models.embed_content(
        model=EMBED_MODEL,
        contents=text,
    )
    return result.embeddings[0].values


def build_embed_text(post: dict) -> str:
    """Combine caption + hashtags into a single string for embedding."""
    hashtags = " ".join(f"#{h}" for h in (post.get("hashtags") or []))
    return f"{post['caption']}\n{hashtags}".strip()


def main():
    # Create table
    Base.metadata.create_all(bind=engine)
    print("✅ caption_examples table ready")

    # Load scraped posts
    with open(INPUT, encoding="utf-8") as f:
        posts = json.load(f)
    print(f"📂 Loaded {len(posts)} posts from {INPUT}")

    gemini = genai.Client(api_key=GOOGLE_API_KEY)
    db: Session = SessionLocal()

    # Check if already ingested
    existing = db.query(CaptionExample).count()
    if existing > 0:
        print(f"⚠️  {existing} examples already in DB. Skipping ingestion.")
        print("   Delete rows from caption_examples to re-ingest.")
        db.close()
        return

    print(f"🔢 Embedding {len(posts)} posts with {EMBED_MODEL}...")

    for i, post in enumerate(posts):
        text = build_embed_text(post)
        vector = embed_text(gemini, text)

        example = CaptionExample(
            account=post["account"],
            likes=post["likes"],
            comments=post["comments"],
            engagement_tier=post["engagement_tier"],
            caption=post["caption"],
            hashtags=post["hashtags"],
            embed_text=text,
            embedding=vector,
        )
        db.add(example)

        tier = post["engagement_tier"]
        print(f"  [{i+1:2d}/50] [{tier:5s}] @{post['account']} — {post['likes']} likes")

    db.commit()
    db.close()

    print(f"\n✅ Ingested {len(posts)} caption examples into pgvector")
    print(f"   Embedding model: {EMBED_MODEL} ({VECTOR_DIM}d)")


if __name__ == "__main__":
    main()
