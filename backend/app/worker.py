from celery import Celery
from app.config import settings

celery_app = Celery("second_brain", broker = settings.redis_url, include = ["app.tasks"],)
celery_app.conf.update(tasks_acks_late=True, worker_prefetch_multiplier=1)
