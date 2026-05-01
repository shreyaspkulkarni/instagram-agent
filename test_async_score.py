"""
Test the Celery photo scoring task.

Runs the task synchronously (no worker needed) using .apply().
To test with a real worker:
  Terminal 1: uv run celery -A backend.celery_app worker --loglevel=info
  Terminal 2: uv run python test_async_score.py --live
"""

import sys
import time
from pathlib import Path

IMAGE_PATH = "photos/IMG_7245_small.jpeg"
LIVE = "--live" in sys.argv

from backend.db.database import SessionLocal
from backend.db.models import User
from backend.tasks.photo_tasks import score_photo_task

# Get the first user from DB
db = SessionLocal()
user = db.query(User).first()
db.close()

if not user:
    print("No users in DB. Log in via OAuth first.")
    sys.exit(1)

user_id = str(user.id)
print(f"Using user: {user.username} ({user_id})")
print(f"Image: {IMAGE_PATH}\n")

if not Path(IMAGE_PATH).exists():
    print(f"Image not found at {IMAGE_PATH}. Update IMAGE_PATH to a valid photo.")
    sys.exit(1)

# Write a temp copy so the task can delete it without touching the original
import shutil, uuid
from pathlib import Path as P

temp_path = f"photos/temp/{uuid.uuid4()}.jpeg"
P("photos/temp").mkdir(parents=True, exist_ok=True)
shutil.copy(IMAGE_PATH, temp_path)

if LIVE:
    print("Queuing task to live Celery worker...")
    task = score_photo_task.delay(temp_path, user_id, Path(IMAGE_PATH).name)
    print(f"Job ID: {task.id}")
    print("Waiting for result", end="", flush=True)
    start = time.time()
    while not task.ready():
        print(".", end="", flush=True)
        time.sleep(1)
    elapsed = time.time() - start
    result = task.result
else:
    print("Running task synchronously (no worker needed)...")
    start = time.time()
    task = score_photo_task.apply(args=[temp_path, user_id, Path(IMAGE_PATH).name])
    elapsed = time.time() - start
    result = task.result

print(f"\nDone in {elapsed:.1f}s\n")

if isinstance(result, Exception):
    print(f"Task failed: {result}")
    sys.exit(1)

print("=" * 60)
print(f"Photo ID:     {result['photo_id']}")
print(f"Score:        {result['score']}/10")
print(f"Post worthy:  {result['post_worthy']}")
print(f"Format:       {result['recommended_format']}")
print(f"Subject:      {result['subject_notes']}")
print(f"\nEdit suggestions:")
for s in result["edit_suggestions"]:
    print(f"  - {s}")
print("=" * 60)
