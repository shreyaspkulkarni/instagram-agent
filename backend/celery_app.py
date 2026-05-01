from celery import Celery

from backend.config import settings

celery = Celery(
    "instagram_agent",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["backend.tasks.photo_tasks"],
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    result_expires=3600,
    task_track_started=True,
    # solo pool avoids fork() segfaults with native libs (Pillow, Google AI SDK) on macOS
    worker_pool="solo",
)
