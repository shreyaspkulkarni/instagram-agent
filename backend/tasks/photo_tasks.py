import asyncio
import os

from backend.celery_app import celery
from backend.db.database import SessionLocal
from backend.db.models import Photo
from backend.vision.scorer import score_photo


@celery.task(bind=True, name="tasks.score_photo")
def score_photo_task(self, image_path: str, user_id: str, filename: str) -> dict:
    """Score a photo with Gemini vision. Runs in the background — saves result to DB."""
    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
    finally:
        if os.path.exists(image_path):
            os.remove(image_path)

    # score_photo is async but the underlying Gemini call is synchronous
    score = asyncio.run(score_photo(image_bytes, filename))

    db = SessionLocal()
    try:
        photo = Photo(
            user_id=user_id,
            original_filename=filename,
            score=score.score,
            composition_notes=score.composition_notes,
            lighting_notes=score.lighting_notes,
            subject_notes=score.subject_notes,
            niche_fit=score.niche_fit,
            edit_suggestions=score.edit_suggestions,
            edit_params=score.edit_params.model_dump(),
            recommended_format=score.recommended_format,
            post_worthy=score.post_worthy,
            status="scored",
        )
        db.add(photo)
        db.commit()
        db.refresh(photo)

        return {
            "photo_id": str(photo.id),
            "filename": filename,
            "score": score.score,
            "post_worthy": score.post_worthy,
            "recommended_format": score.recommended_format,
            "composition_notes": score.composition_notes,
            "lighting_notes": score.lighting_notes,
            "subject_notes": score.subject_notes,
            "niche_fit": score.niche_fit,
            "edit_suggestions": score.edit_suggestions,
            "edit_params": score.edit_params.model_dump(),
        }
    finally:
        db.close()
