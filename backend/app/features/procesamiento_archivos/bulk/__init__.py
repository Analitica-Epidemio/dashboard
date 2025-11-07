"""
Bulk processors for epidemiological data.

Modular structure organized by domain:
  bulk/
  ├── main.py                      ← Main orchestrator (start here)
  ├── shared.py                    ← Shared utilities
  ├── ciudadanos/                  ← Citizen processors
  │   ├── __init__.py              ← CiudadanosManager
  │   ├── processor.py             ← Core citizen operations
  │   ├── domicilios.py            ← Address operations
  │   ├── viajes.py                ← Trip operations
  │   └── comorbilidades.py        ← Comorbidity operations
  ├── eventos/                     ← Event processors
  │   ├── __init__.py
  │   ├── processor.py
  │   └── catalogs.py
  ├── establecimientos/            ← Establishment processors
  │   ├── __init__.py
  │   └── processor.py
  ├── diagnosticos/                ← Diagnostic processors
  │   ├── __init__.py
  │   └── processor.py
  ├── salud/                       ← Health processors
  │   ├── __init__.py              ← SaludManager
  │   ├── muestras.py              ← Sample operations
  │   └── vacunas.py               ← Vaccine operations
  └── investigaciones/             ← Investigation processors
      ├── __init__.py
      └── processor.py

USAGE:
  from app.features.procesamiento_archivos.bulk import MainProcessor

  processor = MainProcessor(context, logger)
  results = processor.process_all(dataframe)
"""

from .main import MainProcessor
from .shared import BulkOperationResult, BulkProcessorBase

# Domain managers and processors (for direct access if needed)
from .ciudadanos import CiudadanosManager
from .diagnosticos import DiagnosticosProcessor
from .establecimientos import EstablecimientosProcessor
from .eventos import EventosManager
from .investigaciones import InvestigacionesProcessor
from .salud import SaludManager

__all__ = [
    # Main entry point
    "MainProcessor",
    # Shared utilities
    "BulkProcessorBase",
    "BulkOperationResult",
    # Domain managers and processors (rarely used directly)
    "CiudadanosManager",
    "DiagnosticosProcessor",
    "EstablecimientosProcessor",
    "EventosManager",
    "InvestigacionesProcessor",
    "SaludManager",
]
