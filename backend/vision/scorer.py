import base64
import io

from google import genai
from google.genai import types
from PIL import Image

from backend.config import settings
from backend.vision.schemas import PhotoScore

MAX_DIMENSION = 1024

_client = genai.Client(api_key=settings.google_api_key)

SCORE_PROMPT = """You are an expert Instagram photographer and content strategist.
Analyze this photo and score it for Instagram performance.

Be specific and honest in your notes — this helps the photographer improve.
Consider: composition, lighting quality, subject clarity, visual appeal, and
how well it fits a travel/lifestyle/photography niche on Instagram.

Return a score from 0–10 where:
  9–10 = viral potential, post immediately
  7–8  = strong photo, worth posting with minor edits
  5–6  = decent but needs meaningful edits or better timing
  0–4  = not ready for Instagram"""


def _resize_for_scoring(image_bytes: bytes) -> bytes:
    """Resize to max 1024px, convert to JPEG."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


async def score_photo(image_bytes: bytes, filename: str) -> PhotoScore:
    """Score a photo using Gemini 2.5 Flash (thinking disabled) with structured output."""
    resized = _resize_for_scoring(image_bytes)

    response = _client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=resized, mime_type="image/jpeg"),
            SCORE_PROMPT,
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=PhotoScore,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        ),
    )

    return PhotoScore.model_validate_json(response.text)
