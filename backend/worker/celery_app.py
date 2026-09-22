from celery import Celery
import os

# Configuración básica de Celery usando Redis (por defecto en localhost)
# Se puede sobreescribir con variables de entorno
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "gemelo_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['backend.worker.tasks']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Mexico_City',
    enable_utc=True,
)
