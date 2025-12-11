"""
Dominio de jobs - Gestión de trabajos asíncronos.

Procesamiento asíncrono con Celery, tracking de jobs,
dispatch via registry pattern.
"""

from .constants import JobPriority, JobStatus
from .models import Job

__all__ = [
    "Job",
    "JobStatus",
    "JobPriority",
]
