"""Configuración de Celery para tareas asíncronas."""

from celery import Celery

from app.core.config import settings

# Crear instancia de Celery
celery_app = Celery(
    "epidemiologia",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks"],  # Importar módulo de tareas
)

# Configuración
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Argentina/Buenos_Aires",
    enable_utc=True,
    result_expires=3600,  # 1 hora
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutos máximo por tarea
    task_soft_time_limit=25 * 60,  # Warning a los 25 minutos
)

# Configurar rutas de tareas
celery_app.conf.task_routes = {
    "app.tasks.process_file": "file_processing",
    "app.tasks.generate_report": "reports",
}