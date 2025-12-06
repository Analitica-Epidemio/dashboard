"""
Reports schemas
"""

from typing import Dict, List

from pydantic import BaseModel


class FilterCombination(BaseModel):
    """Modelo para una combinación de filtros"""

    id: str
    group_id: int | None = None
    group_name: str | None = None
    event_ids: List[int] = []
    event_names: List[str] = []
    clasificaciones: List[str] | None = None


class ReportRequest(BaseModel):
    """Request para generar un reporte"""

    date_range: Dict[str, str]  # {"from": "2024-01-01", "to": "2024-12-31"}
    combinations: List[FilterCombination]
    format: str = "pdf"  # solo PDF con Playwright
