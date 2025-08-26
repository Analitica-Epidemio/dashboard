"""Schemas para el dominio de uploads - arquitectura moderna."""

from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from app.domains.uploads.models import JobStatus


class JobStatusResponse(BaseModel):
    """Respuesta del estado de un job asíncrono."""
    
    job_id: str = Field(..., description="UUID del job")
    status: JobStatus = Field(..., description="Estado actual del job")
    progress_percentage: int = Field(..., description="Progreso (0-100)")
    current_step: Optional[str] = Field(None, description="Paso actual")
    total_steps: int = Field(..., description="Total de pasos")
    completed_steps: int = Field(..., description="Pasos completados")
    
    # Timestamps
    created_at: datetime = Field(..., description="Momento de creación")
    started_at: Optional[datetime] = Field(None, description="Momento de inicio")
    completed_at: Optional[datetime] = Field(None, description="Momento de finalización")
    duration_seconds: Optional[float] = Field(None, description="Duración en segundos")
    
    # Errores
    error_message: Optional[str] = Field(None, description="Mensaje de error si falló")
    
    # Resultados (solo si completado exitosamente)
    result_data: Optional[Dict[str, Any]] = Field(None, description="Datos del resultado")


class AsyncJobResponse(BaseModel):
    """Respuesta cuando se inicia un job asíncrono."""
    
    job_id: str = Field(..., description="UUID del job para seguimiento")
    status: JobStatus = Field(..., description="Estado inicial del job")
    message: str = Field(..., description="Mensaje informativo")
    polling_url: str = Field(..., description="URL para consultar estado")


class SheetUploadResponse(BaseModel):
    """Legacy - mantener compatibilidad temporal."""
    
    upload_id: int = Field(..., description="ID único del upload")
    filename: str = Field(..., description="Nombre del archivo original")
    sheet_name: str = Field(..., description="Nombre de la hoja procesada")
    file_path: str = Field(..., description="Ruta donde se guardó el archivo")
    file_size: int = Field(..., description="Tamaño del archivo en bytes")
    total_rows: int = Field(..., description="Total de filas procesadas")
    columns: List[str] = Field(..., description="Nombres de las columnas detectadas")
    upload_timestamp: str = Field(..., description="Timestamp del upload")
    success: bool = Field(..., description="Si el procesamiento fue exitoso")
    message: str = Field(..., description="Mensaje del resultado")