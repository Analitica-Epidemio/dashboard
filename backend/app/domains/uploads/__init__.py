"""
Dominio de uploads - Manejo de archivos subidos.

Procesamiento asíncrono con Celery, tracking de jobs y 
arquitectura moderna sin legacy code.
"""

# Importar modelos para que SQLModel/Alembic los detecte
from .models import ProcessingJob, JobStatus, JobPriority

__all__ = [
    "ProcessingJob",
    "JobStatus", 
    "JobPriority",
]