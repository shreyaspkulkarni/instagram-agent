from google import genai
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.config import settings

_gemini = genai.Client(api_key=settings.google_api_key)
EMBED_MODEL = "models/gemini-embedding-001"


def embed(query: str) -> list[float]:
    result = _gemini.models.embed_content(model=EMBED_MODEL, contents=query)
    return result.embeddings[0].values


def retrieve_similar_captions(db: Session, query: str, top_k: int = 4) -> list[dict]:
    """Find top_k caption examples semantically similar to query, ranked by engagement."""
    vec = embed(query)

    rows = db.execute(text("""
        SELECT account, engagement_tier, likes, caption, hashtags,
               embedding <=> CAST(:vec AS vector) AS distance
        FROM caption_examples
        ORDER BY distance
        LIMIT :k
    """), {"vec": str(vec), "k": top_k}).fetchall()

    return [
        {
            "account": r.account,
            "engagement_tier": r.engagement_tier,
            "likes": r.likes,
            "caption": r.caption,
            "hashtags": r.hashtags,
        }
        for r in rows
    ]
