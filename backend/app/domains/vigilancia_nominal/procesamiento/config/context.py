"""
Contexto simplificado para procesamiento de archivos epidemiológicos.
"""

import logging
from typing import Callable, Optional

from sqlmodel import Session

logger = logging.getLogger(__name__)


class ProcessingContext:
    """Contexto compartido para el procesamiento bulk."""

    def __init__(
        self,
        session: Session,
        progress_callback: Optional[Callable[[int, str], None]] = None,
        batch_size: int = 1000,
    ):
        self.session = session
        self.progress_callback = progress_callback
        self.batch_size = batch_size

    def update_progress(self, percentage: int, message: str) -> None:
        """Actualiza el progreso del procesamiento."""
        if self.progress_callback:
            try:
                self.progress_callback(percentage, message)
            except Exception as e:
                logger.warning(f"Error en callback de progreso: {e}")
