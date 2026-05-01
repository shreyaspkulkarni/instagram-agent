from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.api.deps import get_default_user_id
from backend.captions.generator import generate_caption
from backend.db.database import get_db
from backend.db.models import Photo, Post

router = APIRouter(prefix="/captions", tags=["captions"])


@router.post("/{photo_id}")
async def create_caption(
    photo_id: str,
    db: Session = Depends(get_db),
):
    """Generate a caption for an approved photo. Saves as a Post draft."""
    user_id = get_default_user_id(db)

    photo = db.query(Photo).filter(Photo.id == photo_id, Photo.user_id == user_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    if photo.status != "approved":
        raise HTTPException(status_code=400, detail="Photo must be approved before generating a caption")

    draft = await generate_caption(photo, db)

    post = Post(
        user_id=user_id,
        photo_id=photo_id,
        caption=draft.caption,
        hashtags=" ".join(f"#{h}" for h in draft.hashtags),
        status="draft",
    )
    db.add(post)
    db.commit()
    db.refresh(post)

    return {
        "post_id": str(post.id),
        "caption": draft.caption,
        "hashtags": draft.hashtags,
        "style_notes": draft.style_notes,
    }


@router.get("/drafts")
def list_drafts(db: Session = Depends(get_db)):
    """List all caption drafts."""
    user_id = get_default_user_id(db)
    posts = db.query(Post).filter(Post.user_id == user_id).order_by(Post.created_at.desc()).all()

    return {
        "drafts": [
            {
                "post_id": str(p.id),
                "photo_id": str(p.photo_id) if p.photo_id else None,
                "caption": p.caption,
                "hashtags": p.hashtags,
                "status": p.status,
                "created_at": p.created_at.isoformat(),
            }
            for p in posts
        ]
    }
