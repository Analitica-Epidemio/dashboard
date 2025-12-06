"""
Processor Registry - Desacopla jobs de dominios específicos.

Permite que cada dominio registre su processor sin que jobs
tenga imports directos.

Usage:
    # En vigilancia_nominal/procesamiento/__init__.py
    from app.domains.jobs.registry import register_processor
    from .processor import create_processor
    register_processor("vigilancia_nominal", create_processor)

    # En jobs/tasks.py
    from app.domains.jobs.registry import get_processor
    processor_factory = get_processor("vigilancia_nominal")
    processor = processor_factory(session, progress_callback)
"""

import logging
from typing import Any, Callable, Dict, Optional, Protocol

logger = logging.getLogger(__name__)


class ProcessorProtocol(Protocol):
    """Contrato que todos los processors deben cumplir."""

    def procesar_archivo(self, ruta_archivo: Any, nombre_hoja: Optional[str] = None) -> Dict[str, Any]:
        """Procesa un archivo y retorna resultados."""
        ...


# Type alias para factory functions
ProcessorFactory = Callable[[Any, Callable[[int, str], None]], ProcessorProtocol]

# Registry interno
_processors: Dict[str, ProcessorFactory] = {}


def register_processor(name: str, factory: ProcessorFactory) -> None:
    """
    Registra un processor factory.

    Args:
        name: Nombre único del processor (ej: "vigilancia_nominal")
        factory: Función que crea el processor. Signature:
                 factory(session, progress_callback) -> ProcessorProtocol
    """
    if name in _processors:
        logger.warning(f"Processor '{name}' ya registrado, sobrescribiendo")

    _processors[name] = factory
    logger.info(f"✅ Processor registrado: {name}")


def get_processor(name: str) -> ProcessorFactory:
    """
    Obtiene un processor factory por nombre.

    Args:
        name: Nombre del processor registrado

    Returns:
        Factory function para crear el processor

    Raises:
        KeyError: Si el processor no está registrado
    """
    if name not in _processors:
        available = list(_processors.keys())
        raise KeyError(
            f"Processor '{name}' no registrado. "
            f"Disponibles: {available}. "
            f"¿Olvidaste importar el módulo del dominio?"
        )

    return _processors[name]


def list_processors() -> list[str]:
    """Lista todos los processors registrados."""
    return list(_processors.keys())


def is_registered(name: str) -> bool:
    """Verifica si un processor está registrado."""
    return name in _processors
