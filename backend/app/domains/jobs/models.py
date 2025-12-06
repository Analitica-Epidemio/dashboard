"""
Modelos genéricos para el dominio de jobs.

Este modelo es agnóstico al tipo de trabajo - toda la información
específica va en input_data/output_data JSON.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlmodel import JSON, Column, Field

from app.core.models import BaseModel
from app.domains.jobs.constants import JobPriority, JobStatus


class Job(BaseModel, table=True):
    """
    Modelo genérico para tracking de trabajos asíncronos.

    Toda la información específica del tipo de trabajo va en:
    - input_data: Datos de entrada (ej: filename, sheet_name, etc.)
    - output_data: Resultados (ej: rows_processed, entities_created, etc.)

    Esto permite usar el mismo modelo para:
    - Procesamiento de archivos
    - Generación de reportes
    - Cualquier otro job futuro
    """

    __tablename__ = "jobs"

    # === Identificación ===
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        description="UUID único del trabajo",
    )
    job_type: str = Field(
        ...,
        description="Tipo de trabajo (file_processing, report_generation, etc.)",
    )
    processor_type: Optional[str] = Field(
        default=None,
        description="Tipo de processor a usar (vigilancia_nominal, vigilancia_agregada, etc.)",
    )

    # === Estado y progreso ===
    status: JobStatus = Field(default=JobStatus.PENDING, description="Estado actual")
    priority: JobPriority = Field(default=JobPriority.NORMAL, description="Prioridad")
    progress_percentage: int = Field(
        default=0, description="Porcentaje de completado (0-100)"
    )
    current_step: Optional[str] = Field(
        default=None, description="Descripción del paso actual"
    )
    total_steps: int = Field(default=1, description="Total de pasos estimados")
    completed_steps: int = Field(default=0, description="Pasos completados")

    # === Datos genéricos (JSON) ===
    input_data: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Datos de entrada específicos del job_type",
    )
    output_data: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Resultados específicos del job_type",
    )

    # === Errores ===
    error_message: Optional[str] = Field(
        default=None, description="Mensaje de error si falla"
    )
    error_traceback: Optional[str] = Field(
        default=None, description="Traceback completo del error"
    )

    # === Timestamps ===
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

    # === Celery ===
    celery_task_id: Optional[str] = Field(
        default=None, description="ID de la task de Celery"
    )

    # === Usuario ===
    created_by: Optional[str] = Field(
        default=None, description="Usuario que creó el trabajo"
    )

    # === Métodos de actualización ===

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
        elif self.total_steps > 0:
            self.completed_steps = int((percentage / 100) * self.total_steps)
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

        # Merge result_data into output_data
        if result_data:
            self.output_data = {**(self.output_data or {}), **result_data}

    def mark_failed(self, error_message: str, error_traceback: Optional[str] = None):
        """Marca el trabajo como fallido."""
        self.status = JobStatus.FAILED
        self.error_message = error_message
        self.error_traceback = error_traceback
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()

    @property
    def is_finished(self) -> bool:
        """Verifica si el trabajo ya terminó."""
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

    # === Helpers para acceso a input_data ===

    def get_input(self, key: str, default: Any = None) -> Any:
        """Obtiene un valor de input_data."""
        if not self.input_data:
            return default
        return self.input_data.get(key, default)

    def set_input(self, key: str, value: Any):
        """Establece un valor en input_data."""
        if not self.input_data:
            self.input_data = {}
        # IMPORTANTE: Crear nueva referencia para que SQLAlchemy detecte el cambio
        self.input_data = {**self.input_data, key: value}

    def get_output(self, key: str, default: Any = None) -> Any:
        """Obtiene un valor de output_data."""
        if not self.output_data:
            return default
        return self.output_data.get(key, default)
