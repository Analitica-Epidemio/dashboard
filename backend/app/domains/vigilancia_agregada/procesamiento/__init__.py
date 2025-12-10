"""
Procesamiento de vigilancia agregada.

Módulo para importar y procesar archivos de datos agregados del SNVS.

Tipos soportados:
- CLI_P26: Casos clínicos ambulatorios
- CLI_P26_INT: Ocupación hospitalaria IRA
- LAB_P26: Estudios de laboratorio
"""

# Registrar en el registry de jobs
from app.domains.jobs.registry import register_processor

from .processor import AgregadaProcessor, crear_procesador
from .types import (
    CLIP26IntProcessor,
    CLIP26Processor,
    FileTypeProcessor,
    LabP26Processor,
)
from .types.base_type import ProcessingResult

register_processor("vigilancia_agregada", crear_procesador)

__all__ = [
    "AgregadaProcessor",
    "crear_procesador",
    "FileTypeProcessor",
    "ProcessingResult",
    "CLIP26Processor",
    "CLIP26IntProcessor",
    "LabP26Processor",
]
