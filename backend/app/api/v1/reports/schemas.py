"""
Reports schemas
"""


from pydantic import BaseModel


class FilterCombination(BaseModel):
    """Modelo para una combinación de filtros"""

    id: str
    group_id: int | None = None
    group_name: str | None = None
    event_ids: list[int] = []
    event_names: list[str] = []
    clasificaciones: list[str] | None = None


class ReportRequest(BaseModel):
    """Request para generar un reporte"""

    date_range: dict[str, str]  # {"from": "2024-01-01", "to": "2024-12-31"}
    combinations: list[FilterCombination]
    format: str = "pdf"  # solo PDF con Playwright
