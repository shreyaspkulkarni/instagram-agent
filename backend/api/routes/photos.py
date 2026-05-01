import uuid
from pathlib import Path

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.api.deps import get_default_user_id
from backend.celery_app import celery as celery_app
from backend.db.database import get_db
from backend.db.models import Photo
from backend.tasks.photo_tasks import score_photo_task

router = APIRouter(prefix="/photos", tags=["photos"])

SUPPORTED_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/heic"}
MAX_FILE_SIZE_MB = 20
TEMP_DIR = Path("photos/temp")


@router.post("/score")
async def score_photos(
    files: list[UploadFile],
    db: Session = Depends(get_db),
):
    """
    Upload 1–10 photos. Each is queued as a background job — returns job IDs immediately.
    Poll GET /photos/jobs/{job_id} to check status and get results.
    """
    user_id = get_default_user_id(db)

    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Max 10 photos per request")

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    jobs = []

    for file in files:
        if file.content_type not in SUPPORTED_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"{file.filename}: unsupported type. Supported: JPEG, PNG, WEBP, HEIC",
            )

        image_bytes = await file.read()
        if len(image_bytes) > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"{file.filename}: file too large (max {MAX_FILE_SIZE_MB}MB)",
            )

        ext = Path(file.filename).suffix or ".jpg"
        temp_path = str(TEMP_DIR / f"{uuid.uuid4()}{ext}")
        with open(temp_path, "wb") as f:
            f.write(image_bytes)

        task = score_photo_task.delay(temp_path, user_id, file.filename)
        jobs.append({"filename": file.filename, "job_id": task.id})

    return {"queued": len(jobs), "jobs": jobs}


@router.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    """Poll the status of a background scoring job."""
    result = AsyncResult(job_id, app=celery_app)

    if result.state == "PENDING":
        return {"job_id": job_id, "status": "pending"}
    elif result.state == "STARTED":
        return {"job_id": job_id, "status": "processing"}
    elif result.state == "SUCCESS":
        return {"job_id": job_id, "status": "completed", "result": result.result}
    elif result.state == "FAILURE":
        return {"job_id": job_id, "status": "failed", "error": str(result.result)}
    else:
        return {"job_id": job_id, "status": result.state.lower()}


@router.get("/")
def list_photos(
    status: str | None = None,
    db: Session = Depends(get_db),
):
    """List all scored photos, optionally filtered by status."""
    user_id = get_default_user_id(db)
    query = db.query(Photo).filter(Photo.user_id == user_id)
    if status:
        query = query.filter(Photo.status == status)
    photos = query.order_by(Photo.score.desc()).all()

    return {
        "photos": [
            {
                "photo_id": str(p.id),
                "filename": p.original_filename,
                "score": p.score,
                "post_worthy": p.post_worthy,
                "status": p.status,
                "recommended_format": p.recommended_format,
                "edit_suggestions": p.edit_suggestions,
                "edit_params": p.edit_params,
                "created_at": p.created_at.isoformat(),
            }
            for p in photos
        ]
    }


@router.patch("/{photo_id}/status")
def update_photo_status(
    photo_id: str,
    status: str,
    db: Session = Depends(get_db),
):
    """Approve or reject a scored photo."""
    user_id = get_default_user_id(db)

    if status not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="status must be 'approved' or 'rejected'")

    photo = db.query(Photo).filter(Photo.id == photo_id, Photo.user_id == user_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    photo.status = status
    db.commit()
    return {"photo_id": photo_id, "status": status}
