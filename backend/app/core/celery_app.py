"""
Configuración de Celery para procesamiento asíncrono de archivos.

Arquitectura senior-level con:
- Separación de concerns
- Configuración centralizada
- Monitoring y logging
- Error handling robusto
"""

import logging

from celery import Celery

from app.core.config import settings

logger = logging.getLogger(__name__)


def create_celery_app() -> Celery:
    """
    Factory function para crear la aplicación Celery.
    Permite configuración flexible y testing.
    """

    celery_app = Celery(
        "epidemiologia_dashboard",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
        include=[
            "app.domains.uploads.tasks",
            # Agregar más módulos de tasks aquí
        ],
    )

    # Configuración optimizada para procesamiento de archivos
    celery_app.conf.update(
        # Serialización
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="America/Argentina/Buenos_Aires",
        enable_utc=True,
        # Workers configuration
        worker_prefetch_multiplier=1,  # Para tasks de archivos grandes
        task_acks_late=True,  # ACK después de completar
        worker_disable_rate_limits=False,
        # Results configuration
        result_expires=3600,  # 1 hora
        result_persistent=True,
        task_track_started=True,
        # Task routing y priority
        task_default_queue="default",
        task_routes={
            "app.domains.uploads.tasks.process_csv_file": {
                "queue": "file_processing",
                "priority": 5,
            },
            "app.domains.uploads.tasks.cleanup_old_files": {
                "queue": "maintenance",
                "priority": 1,
            },
        },
        # Error handling
        task_reject_on_worker_lost=True,
        task_ignore_result=False,
        # Monitoring
        worker_send_task_events=True,
        task_send_sent_event=True,
        # Security
        worker_hijack_root_logger=False,
        worker_log_color=False,
        # File processing specific
        task_soft_time_limit=300,  # 5 minutos soft limit
        task_time_limit=600,  # 10 minutos hard limit
        # Beat scheduler (para tareas periódicas)
        beat_schedule={
            "cleanup-old-files": {
                "task": "app.domains.uploads.tasks.cleanup_old_files",
                "schedule": 3600.0,  # Cada hora
                "options": {"queue": "maintenance"},
            },
            "cleanup-old-jobs": {
                "task": "app.domains.uploads.tasks.cleanup_old_jobs",
                "schedule": 7200.0,  # Cada 2 horas
                "options": {"queue": "maintenance"},
            },
        },
    )

    return celery_app


# Instancia global de Celery
celery_app = create_celery_app()


# Task decorators para conveniencia
def file_processing_task(*args, **kwargs):
    """Decorator para tasks de procesamiento de archivos."""
    return celery_app.task(
        bind=True,
        queue="file_processing",
        soft_time_limit=300,
        time_limit=600,
        *args,
        **kwargs,
    )


def maintenance_task(*args, **kwargs):
    """Decorator para tasks de mantenimiento."""
    return celery_app.task(
        bind=True,
        queue="maintenance",
        soft_time_limit=60,
        time_limit=120,
        *args,
        **kwargs,
    )


# Health check para monitoring
@celery_app.task(name="app.core.celery_app.health_check")
def health_check():
    """Task simple para verificar que Celery está funcionando."""
    return {"status": "healthy", "message": "Celery is running"}


if __name__ == "__main__":
    # Para ejecutar worker desde línea de comandos
    celery_app.start()
