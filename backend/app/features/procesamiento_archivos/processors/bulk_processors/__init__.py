"""
Bulk processors divididos por dominio para mejor mantenabilidad.

Cada módulo se enfoca en un dominio específico del sistema epidemiológico,
siguiendo screaming architecture para hacer evidente la funcionalidad.
"""

from .base import BulkProcessorBase
from .ciudadanos import CiudadanosBulkProcessor
from .diagnosticos import DiagnosticosBulkProcessor
from .establecimientos import EstablecimientosBulkProcessor
from .eventos import EventosBulkProcessor
from .investigaciones import InvestigacionesBulkProcessor
from .main_processor import MainBulkProcessor
from .result import BulkOperationResult
from .salud import SaludBulkProcessor

__all__ = [
    "BulkProcessorBase",
    "BulkOperationResult",
    "CiudadanosBulkProcessor",
    "DiagnosticosBulkProcessor", 
    "EstablecimientosBulkProcessor",
    "EventosBulkProcessor",
    "InvestigacionesBulkProcessor",
    "MainBulkProcessor", 
    "SaludBulkProcessor",
]