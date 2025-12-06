"""
Validación genérica de archivos.

Provee validación de:
- Extensiones permitidas
- Tamaño máximo
- MIME type real (magic bytes)
"""

import logging
from typing import Set

import magic
from fastapi import HTTPException, UploadFile

logger = logging.getLogger(__name__)


class FileValidator:
    """Validador genérico de archivos."""

    # MIME types conocidos
    SPREADSHEET_MIMES = {
        "text/csv",
        "text/plain",
        "application/csv",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }

    IMAGE_MIMES = {
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
    }

    def __init__(self, max_size_mb: int = 50):
        self.max_size_bytes = max_size_mb * 1024 * 1024

    async def validar(
        self,
        archivo: UploadFile,
        extensiones_permitidas: Set[str],
        mimes_permitidos: Set[str],
    ) -> bytes:
        """
        Validar archivo.

        Args:
            archivo: Archivo a validar
            extensiones_permitidas: Extensiones permitidas (ej: {".csv", ".xlsx"})
            mimes_permitidos: MIME types permitidos

        Returns:
            bytes: Contenido del archivo

        Raises:
            HTTPException: Si la validación falla
        """
        if not archivo.filename:
            raise HTTPException(status_code=400, detail="Nombre de archivo inválido")

        # Validar extensión
        ext = "." + archivo.filename.lower().split(".")[-1] if "." in archivo.filename else ""
        if ext not in extensiones_permitidas:
            raise HTTPException(
                status_code=400,
                detail=f"Extensión no permitida. Permitidas: {', '.join(extensiones_permitidas)}"
            )

        # Leer contenido
        contenido = await archivo.read()
        await archivo.seek(0)

        # Validar tamaño
        if len(contenido) > self.max_size_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"Archivo demasiado grande. Máximo: {self.max_size_bytes / (1024 * 1024):.0f}MB",
            )

        # Validar MIME type real
        mime_detectado = magic.from_buffer(contenido, mime=True)
        if mime_detectado not in mimes_permitidos:
            logger.warning(f"MIME inválido: {mime_detectado} para {archivo.filename}")
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de archivo no válido. MIME detectado: {mime_detectado}"
            )

        logger.debug(f"Archivo validado: {archivo.filename}, MIME: {mime_detectado}")
        return contenido

    async def validar_planilla(self, archivo: UploadFile) -> bytes:
        """Validar archivo de hoja de cálculo (CSV/Excel)."""
        return await self.validar(
            archivo,
            extensiones_permitidas={".csv", ".xlsx", ".xls"},
            mimes_permitidos=self.SPREADSHEET_MIMES,
        )

    async def validar_imagen(self, archivo: UploadFile) -> bytes:
        """Validar imagen."""
        return await self.validar(
            archivo,
            extensiones_permitidas={".jpg", ".jpeg", ".png", ".gif", ".webp"},
            mimes_permitidos=self.IMAGE_MIMES,
        )


# Singleton
file_validator = FileValidator()
