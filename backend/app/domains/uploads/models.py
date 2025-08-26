"""Modelos para el dominio de uploads."""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class FileUpload(SQLModel, table=True):
    """Registro de archivos subidos."""
    
    __tablename__ = "file_uploads"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str = Field(..., description="Nombre original del archivo")
    file_path: str = Field(..., description="Ruta donde se guardó el archivo")
    file_size: int = Field(..., description="Tamaño en bytes")
    selected_sheet: str = Field(..., description="Nombre de la hoja seleccionada")
    total_sheets: int = Field(..., description="Total de hojas en el archivo")
    total_rows_processed: int = Field(..., description="Filas procesadas de la hoja seleccionada")
    upload_timestamp: datetime = Field(default_factory=datetime.now)
    processed: bool = Field(default=False, description="Si se procesó completamente")
    
    # Metadata adicional
    mime_type: Optional[str] = Field(default=None)
    uploaded_by: Optional[str] = Field(default=None, description="ID del usuario que subió")
    processing_notes: Optional[str] = Field(default=None, description="Notas del procesamiento")