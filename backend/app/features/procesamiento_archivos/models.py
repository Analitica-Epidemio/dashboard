"""Modelos para el dominio de uploads."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlmodel import JSON, Column, Field

from app.core.models import BaseModel


class JobStatus(str, Enum):
    """Estados posibles de un trabajo de procesamiento."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobPriority(int, Enum):
    """Prioridades para trabajos."""

    LOW = 1
    NORMAL = 3
    HIGH = 5
    URGENT = 7


class ProcessingJob(BaseModel, table=True):
    """
    Modelo para tracking de trabajos de procesamiento asíncrono.
    Arquitectura senior-level con estados, progreso y metadata.
    """

    __tablename__ = "processing_jobs"

    # Identificación
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        description="UUID único del trabajo",
    )

    # Información básica
    job_type: str = Field(..., description="Tipo de trabajo (csv_processing, etc.)")
    status: JobStatus = Field(default=JobStatus.PENDING, description="Estado actual")
    priority: JobPriority = Field(default=JobPriority.NORMAL, description="Prioridad")

    # Progreso
    progress_percentage: int = Field(
        default=0, description="Porcentaje de completado (0-100)"
    )
    current_step: Optional[str] = Field(
        default=None, description="Paso actual de procesamiento"
    )
    total_steps: int = Field(default=1, description="Total de pasos para este trabajo")
    completed_steps: int = Field(default=0, description="Pasos completados")

    # Archivos
    original_filename: str = Field(..., description="Nombre del archivo original")
    file_path: Optional[str] = Field(
        default=None, description="Ruta del archivo procesado"
    )
    file_size: Optional[int] = Field(
        default=None, description="Tamaño del archivo en bytes"
    )
    sheet_name: Optional[str] = Field(
        default=None, description="Nombre de la hoja procesada"
    )

    # Resultados
    total_rows: Optional[int] = Field(
        default=None, description="Total de filas procesadas"
    )
    columns: Optional[List[str]] = Field(
        default=None, sa_column=Column(JSON), description="Columnas del archivo"
    )
    validation_errors: Optional[List[str]] = Field(
        default=None, sa_column=Column(JSON), description="Errores de validación"
    )

    # Metadata y tracking
    job_metadata: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON), description="Metadata adicional"
    )
    error_message: Optional[str] = Field(
        default=None, description="Mensaje de error si falla"
    )
    error_traceback: Optional[str] = Field(
        default=None, description="Traceback completo del error"
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.now, description="Momento de creación"
    )
    started_at: Optional[datetime] = Field(
        default=None, description="Momento de inicio"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="Momento de finalización"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now, description="Última actualización"
    )

    # Celery específico
    celery_task_id: Optional[str] = Field(
        default=None, description="ID de la task de Celery"
    )

    # Usuario
    created_by: Optional[str] = Field(
        default=None, description="Usuario que creó el trabajo"
    )

    def update_progress(
        self,
        percentage: int,
        step: Optional[str] = None,
        increment_completed_steps: bool = False,
    ):
        """Actualiza el progreso del trabajo."""
        self.progress_percentage = max(0, min(100, percentage))
        if step:
            self.current_step = step
        if increment_completed_steps:
            self.completed_steps += 1
        self.updated_at = datetime.now()

    def mark_started(self, celery_task_id: str):
        """Marca el trabajo como iniciado."""
        self.status = JobStatus.IN_PROGRESS
        self.started_at = datetime.now()
        self.updated_at = datetime.now()
        self.celery_task_id = celery_task_id

    def mark_completed(self, **result_data):
        """Marca el trabajo como completado."""
        self.status = JobStatus.COMPLETED
        self.progress_percentage = 100
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()

        # Actualizar datos del resultado
        if "total_rows" in result_data:
            self.total_rows = result_data["total_rows"]
        if "columns" in result_data:
            self.columns = result_data["columns"]
        if "file_path" in result_data:
            self.file_path = result_data["file_path"]

    def mark_failed(self, error_message: str, error_traceback: Optional[str] = None):
        """Marca el trabajo como fallido."""
        self.status = JobStatus.FAILED
        self.error_message = error_message
        self.error_traceback = error_traceback
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()

    @property
    def is_finished(self) -> bool:
        """Verifica si el trabajo ya terminó (exitoso o fallido)."""
        return self.status in [
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
        ]

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calcula la duración del trabajo en segundos."""
        if not self.started_at:
            return None

        end_time = self.completed_at or datetime.now()
        return (end_time - self.started_at).total_seconds()
