import anthropic
import instructor
from sqlalchemy.orm import Session

from backend.captions.schemas import CaptionDraft
from backend.config import settings
from backend.db.models import Photo
from backend.rag.retriever import retrieve_similar_captions

_client = instructor.from_anthropic(
    anthropic.Anthropic(api_key=settings.anthropic_api_key)
)

SYSTEM_PROMPT = """You are a creative Instagram content strategist specializing in
lifestyle and travel photography. You write captions that feel authentic and personal —
not corporate, not generic. You study what actually drives engagement in this niche
and apply those patterns naturally."""


def _build_prompt(photo: Photo, examples: list[dict]) -> str:
    examples_text = "\n\n".join([
        f"[{e['engagement_tier']} — {e['likes']:,} likes | @{e['account']}]\n{e['caption']}"
        for e in examples
    ])

    hashtag_pool = []
    for e in examples:
        hashtag_pool.extend(e.get("hashtags") or [])
    common_tags = list(dict.fromkeys(hashtag_pool))[:20]

    return f"""Here is a photo that needs an Instagram caption.

PHOTO DETAILS (from AI vision analysis):
- Subject: {photo.subject_notes}
- Composition: {photo.composition_notes}
- Lighting: {photo.lighting_notes}
- Niche fit: {photo.niche_fit}
- Recommended format: {photo.recommended_format}
- Score: {photo.score}/10

HIGH-ENGAGEMENT CAPTION EXAMPLES from similar lifestyle/travel posts:
{examples_text}

COMMON HASHTAGS in this niche: {', '.join(f'#{t}' for t in common_tags)}

Write a caption for this photo. Study the examples above — notice their tone,
length, structure, and what makes them feel natural. Write something original
that fits this specific photo but resonates with the same audience.

Keep it authentic. Don't be cheesy or overly promotional."""


async def generate_caption(photo: Photo, db: Session) -> CaptionDraft:
    """Generate a caption for an approved photo using RAG + Claude."""
    query = f"{photo.niche_fit} {photo.subject_notes}"
    examples = retrieve_similar_captions(db, query, top_k=4)

    prompt = _build_prompt(photo, examples)

    return _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
        response_model=CaptionDraft,
    )
