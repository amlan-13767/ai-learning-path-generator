"""
Celery application configuration
"""
import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# Redis URL for broker and backend
REDIS_URL = os.getenv('REDIS_URL')
if not REDIS_URL or not REDIS_URL.startswith(('redis://', 'rediss://')):
    # Fallback to individual parameters
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = os.getenv('REDIS_PORT', '6379')
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
    REDIS_DB = os.getenv('REDIS_DB', '0')
    
    if REDIS_PASSWORD:
        REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    else:
        REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# Create Celery app
celery_app = Celery(
    'learning_path_worker',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['worker.tasks']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3300,  # 55 minutes soft limit
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks (prevent memory leaks)
)

if __name__ == '__main__':
    celery_app.start()
