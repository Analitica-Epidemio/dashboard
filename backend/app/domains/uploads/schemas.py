"""Schemas para el dominio de uploads."""

from typing import List, Optional, Any
from pydantic import BaseModel, Field


class SheetUploadResponse(BaseModel):
    """Respuesta del upload de una hoja específica de Excel."""
    
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


class SheetUploadRequest(BaseModel):
    """Metadatos para el upload de hoja."""
    
    original_filename: str = Field(..., description="Nombre del archivo original")
    sheet_name: str = Field(..., description="Nombre de la hoja")
    description: Optional[str] = Field(None, description="Descripción opcional")