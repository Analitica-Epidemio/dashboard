"""
Procesamiento de vigilancia agregada - SKELETON.

Este módulo registra automáticamente el processor en el registry de jobs.
"""

from app.domains.jobs.registry import register_processor

from .processor import crear_procesador

# Registrar processor automáticamente al importar el módulo
register_processor("vigilancia_agregada", crear_procesador)

__all__ = ["crear_procesador"]
