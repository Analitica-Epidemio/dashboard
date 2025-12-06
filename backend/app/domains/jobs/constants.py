"""
Constantes para el dominio de jobs.
"""

from enum import Enum


class JobStatus(str, Enum):
    """Estados posibles de un trabajo."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class JobPriority(int, Enum):
    """Prioridades para trabajos."""

    LOW = 1
    NORMAL = 3
    HIGH = 5
    URGENT = 7
