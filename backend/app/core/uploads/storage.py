"""
Almacenamiento temporal de archivos.

Provee:
- Guardado de archivos temporales
- Generación de nombres únicos
- Limpieza de archivos antiguos
"""

import logging
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile

logger = logging.getLogger(__name__)


class TempFileStorage:
    """Almacenamiento temporal de archivos."""

    def __init__(self, directorio_base: str = "uploads"):
        self.directorio_base = Path(directorio_base)
        self.directorio_base.mkdir(exist_ok=True)

    async def guardar(
        self,
        archivo: UploadFile,
        id_unico: str,
        sufijo: Optional[str] = None,
    ) -> Path:
        """
        Guardar archivo temporal.

        Args:
            archivo: Archivo a guardar
            id_unico: ID único (ej: job_id)
            sufijo: Sufijo adicional para el nombre

        Returns:
            Path al archivo guardado
        """
        ext_original = Path(archivo.filename).suffix.lower() if archivo.filename else ""

        if sufijo:
            sufijo_limpio = "".join(
                c for c in sufijo if c.isalnum() or c in (" ", "-", "_")
            ).strip()
            nombre_archivo = f"{id_unico}_{sufijo_limpio}{ext_original}"
        else:
            nombre_archivo = f"{id_unico}{ext_original}"

        ruta_archivo = self.directorio_base / nombre_archivo

        try:
            contenido = await archivo.read()
            with open(ruta_archivo, "wb") as buffer:
                buffer.write(contenido)

            logger.debug(f"Archivo guardado: {ruta_archivo}")
            return ruta_archivo

        except Exception as e:
            if ruta_archivo.exists():
                ruta_archivo.unlink()
            raise HTTPException(
                status_code=500, detail=f"Error guardando archivo: {str(e)}"
            )

    def eliminar(self, ruta_archivo: Path) -> bool:
        """Eliminar archivo."""
        try:
            if ruta_archivo.exists():
                ruta_archivo.unlink()
                return True
            return False
        except Exception as e:
            logger.warning(f"Error eliminando {ruta_archivo}: {e}")
            return False


# Singleton
temp_storage = TempFileStorage()
