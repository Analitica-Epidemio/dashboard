"""Endpoint para buscar establecimientos IGN."""

from typing import Optional

from fastapi import Depends, Query
from sqlmodel import Session

from app.core.database import get_session

from .mapeo_schemas import BuscarIGNResponse
from .suggestions_service import buscar_establecimientos_ign


async def buscar_establecimientos_ign_endpoint(
    q: Optional[str] = Query(None, description="Búsqueda por nombre o código REFES"),
    provincia: Optional[str] = Query(None, description="Filtrar por provincia"),
    departamento: Optional[str] = Query(None, description="Filtrar por departamento"),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(50, ge=1, le=200, description="Resultados por página"),
    session: Session = Depends(get_session),
) -> BuscarIGNResponse:
    """Busca establecimientos IGN con filtros."""
    offset = (page - 1) * page_size

    items, total = await buscar_establecimientos_ign(
        session=session,
        query=q,
        provincia_nombre=provincia,
        departamento_nombre=departamento,
        limit=page_size,
        offset=offset
    )

    return BuscarIGNResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )
