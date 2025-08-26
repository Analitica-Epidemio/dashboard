"""Servicios para el manejo de uploads de hojas Excel individuales."""

import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Any
from fastapi import HTTPException, UploadFile
import magic

from app.domains.uploads.schemas import SheetUploadResponse
from app.domains.uploads.models import FileUpload


class SheetUploadService:
    """Servicio simplificado para manejo de hojas Excel individuales."""
    
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        
        # Límites de archivo
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        
        # Tipos MIME permitidos
        self.allowed_mime_types = {
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel"
        }
    
    def validate_file(self, file: UploadFile) -> None:
        """Valida el archivo subido."""
        
        # Validar tamaño
        if hasattr(file, 'size') and file.size and file.size > self.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"Archivo muy grande. Máximo permitido: {self.max_file_size / (1024*1024):.0f}MB"
            )
        
        # Validar extensión
        if not file.filename or not file.filename.lower().endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=400,
                detail="Solo se permiten archivos Excel (.xlsx, .xls)"
            )
    
    def save_file(self, file: UploadFile, original_filename: str, sheet_name: str) -> Path:
        """Guarda el archivo en el sistema de archivos."""
        
        # Generar nombre único con contexto
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_sheet_name = "".join(c for c in sheet_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{timestamp}_{clean_sheet_name}_{original_filename}"
        file_path = self.upload_dir / filename
        
        # Guardar archivo
        try:
            with open(file_path, "wb") as buffer:
                content = file.file.read()
                buffer.write(content)
                
            return file_path
            
        except Exception as e:
            # Limpiar archivo parcial si hay error
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=500,
                detail=f"Error al guardar archivo: {str(e)}"
            )
    
    def process_sheet_upload(
        self, 
        file: UploadFile, 
        original_filename: str, 
        sheet_name: str
    ) -> SheetUploadResponse:
        """Procesa el upload de una hoja específica de Excel."""
        
        # Validar archivo
        self.validate_file(file)
        
        # Guardar archivo
        file_path = self.save_file(file, original_filename, sheet_name)
        
        try:
            # Leer y procesar la hoja
            df = pd.read_excel(file_path)
            
            # Obtener información de la hoja
            total_rows = len(df)
            columns = df.columns.tolist()
            file_size = file_path.stat().st_size
            
            # Aquí puedes agregar lógica específica de procesamiento de datos
            # Por ejemplo: validaciones, transformaciones, guardado en BD principal
            
            # Simular guardado en BD
            upload_id = int(datetime.now().timestamp())
            
            return SheetUploadResponse(
                upload_id=upload_id,
                filename=original_filename,
                sheet_name=sheet_name,
                file_path=str(file_path),
                file_size=file_size,
                total_rows=total_rows,
                columns=columns,
                upload_timestamp=datetime.now().isoformat(),
                success=True,
                message=f"Hoja '{sheet_name}' procesada exitosamente con {total_rows} filas"
            )
            
        except Exception as e:
            # Limpiar archivo si hay error en el procesamiento
            if file_path.exists():
                file_path.unlink()
                
            raise HTTPException(
                status_code=422,
                detail=f"Error al procesar hoja Excel: {str(e)}"
            )


# Instancia singleton del servicio
sheet_service = SheetUploadService()