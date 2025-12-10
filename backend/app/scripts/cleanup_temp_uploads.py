"""Script para limpiar archivos temporales de uploads."""

import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import TypedDict

logger = logging.getLogger(__name__)


class CleanupResult(TypedDict):
    """Resultado de la limpieza de archivos temporales."""

    deleted_count: int
    deleted_size_mb: float
    errors: list[str]


def cleanup_old_temp_files(
    max_age_hours: int = 1, temp_dir: str | None = None
) -> CleanupResult:
    """
    Limpia archivos temporales de preview que superan la edad máxima.

    Args:
        max_age_hours: Edad máxima en horas para mantener archivos.
        temp_dir: Directorio de archivos temporales. Por defecto usa /tmp/epidemio_preview.

    Returns:
        Diccionario con estadísticas de limpieza.
    """
    if temp_dir is None:
        temp_dir = os.environ.get("TEMP_UPLOAD_DIR", "/tmp/epidemio_preview")

    temp_path = Path(temp_dir)
    result: CleanupResult = {
        "deleted_count": 0,
        "deleted_size_mb": 0.0,
        "errors": [],
    }

    if not temp_path.exists():
        logger.info(f"Directorio temporal no existe: {temp_dir}")
        return result

    cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
    total_size = 0

    try:
        for file_path in temp_path.iterdir():
            if file_path.is_file():
                try:
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_mtime < cutoff_time:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        result["deleted_count"] += 1
                        total_size += file_size
                        logger.debug(f"Eliminado: {file_path.name}")
                except Exception as e:
                    error_msg = f"Error eliminando {file_path.name}: {e}"
                    result["errors"].append(error_msg)
                    logger.warning(error_msg)

        result["deleted_size_mb"] = total_size / (1024 * 1024)
        logger.info(
            f"Limpieza completada: {result['deleted_count']} archivos, "
            f"{result['deleted_size_mb']:.2f} MB liberados"
        )

    except Exception as e:
        error_msg = f"Error durante limpieza: {e}"
        result["errors"].append(error_msg)
        logger.error(error_msg)

    return result


if __name__ == "__main__":
    # Ejecutar limpieza directamente
    import sys

    max_age = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    result = cleanup_old_temp_files(max_age_hours=max_age)
    print(f"Archivos eliminados: {result['deleted_count']}")
    print(f"Espacio liberado: {result['deleted_size_mb']:.2f} MB")
    if result["errors"]:
        print(f"Errores: {len(result['errors'])}")
