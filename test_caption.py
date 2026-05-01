import asyncio
import time

from backend.captions.generator import generate_caption
from backend.db.database import SessionLocal
from backend.db.models import Photo


async def main():
    db = SessionLocal()

    # Find a photo to test with — prefer approved, fall back to scored
    photo = db.query(Photo).filter(Photo.status == "approved").first()
    if not photo:
        photo = db.query(Photo).filter(Photo.status == "scored").first()
        if not photo:
            print("No scored photos in DB. Run test_score_photo.py first.")
            db.close()
            return
        print(f"No approved photos found. Using scored photo: {photo.original_filename}")
        print("Temporarily marking as approved for this test...\n")
        photo.status = "approved"
        db.commit()
        db.refresh(photo)
    else:
        print(f"Using approved photo: {photo.original_filename}\n")

    print(f"Photo details:")
    print(f"  Score:    {photo.score}/10")
    print(f"  Subject:  {photo.subject_notes}")
    print(f"  Niche:    {photo.niche_fit}")
    print(f"  Format:   {photo.recommended_format}")
    print()

    print("Retrieving similar captions from pgvector...")
    print("Calling Claude claude-sonnet-4-6 to generate caption...")
    start = time.time()

    draft = await generate_caption(photo, db)

    elapsed = time.time() - start
    print(f"Done in {elapsed:.1f}s\n")

    print("=" * 60)
    print("CAPTION:")
    print(draft.caption)
    print()
    print("HASHTAGS:")
    print("  " + "  ".join(f"#{h}" for h in draft.hashtags))
    print()
    print("STYLE NOTES:")
    print(f"  {draft.style_notes}")
    print("=" * 60)

    db.close()


asyncio.run(main())
