"""
Processor para vigilancia agregada - SKELETON.

TODO: Implementar lógica de procesamiento de datos agregados.
"""

from pathlib import Path
from typing import Any, Callable, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession


class AgregadaProcessor:
    """
    Processor para datos de vigilancia agregada.

    TODO: Implementar lógica específica para datos agregados.
    """

    def __init__(
        self, session: AsyncSession, callback_progreso: Callable[[int, str], None]
    ) -> None:
        self.session = session
        self.callback_progreso = callback_progreso

    def procesar_archivo(
        self, ruta_archivo: Path, nombre_hoja: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Procesa archivo de vigilancia agregada.

        Args:
            ruta_archivo: Ruta al archivo
            nombre_hoja: Nombre de la hoja (para Excel)

        Returns:
            Diccionario con resultados

        Raises:
            NotImplementedError: Siempre, hasta que se implemente
        """
        raise NotImplementedError(
            "Procesamiento de vigilancia agregada aún no implementado. "
            "Este es un skeleton para futura implementación."
        )


def crear_procesador(
    session: AsyncSession, callback_progreso: Callable[[int, str], None]
) -> AgregadaProcessor:
    """
    Factory function para crear el processor.

    Args:
        session: SQLAlchemy session
        callback_progreso: Callback para reportar progreso

    Returns:
        AgregadaProcessor instance
    """
    return AgregadaProcessor(session, callback_progreso)
