from celery import Celery
from app.core.config import settings

# Initialize Celery app instance
celery_app = Celery(
    "transaction_pipeline",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.worker.tasks"]
)

# Standard configurations
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    # Configure task prefetching (1 = fair routing of tasks)
    worker_prefetch_multiplier=1
)
