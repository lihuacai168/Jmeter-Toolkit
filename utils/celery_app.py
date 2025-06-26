"""Celery application configuration."""
from celery import Celery
from config import settings

# Create Celery instance
celery_app = Celery(
    "jmeter_toolkit",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["utils.tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.jmeter_timeout,
    task_soft_time_limit=settings.jmeter_timeout - 60,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    task_compression="gzip",
    result_compression="gzip",
)