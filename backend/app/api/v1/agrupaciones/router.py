"""
Endpoints de Agrupaciones de Agentes Etiológicos.

Permite listar y gestionar agrupaciones de agentes para visualización.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, col, select

from app.core.database import get_session
from app.core.security import RequireAnyRole
from app.domains.autenticacion.models import User
from app.domains.catalogos.agentes.agrupacion import (
    AgrupacionAgenteLink,
    AgrupacionAgentes,
)
from app.domains.catalogos.agentes.models import AgenteEtiologico

router = APIRouter(prefix="/agrupaciones", tags=["Agrupaciones de Agentes"])


# ═══════════════════════════════════════════════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════


class AgenteSimple(BaseModel):
    """Agente simplificado para respuestas."""

    id: int
    slug: str
    nombre: str
    nombre_corto: str


class AgrupacionListItem(BaseModel):
    """Item de agrupación para listados."""

    id: int
    slug: str
    nombre: str
    nombre_corto: str
    color: str
    categoria: str
    orden: int
    agentes_count: int = Field(description="Cantidad de agentes en la agrupación")


class AgrupacionDetailResponse(BaseModel):
    """Detalle de una agrupación con sus agentes."""

    id: int
    slug: str
    nombre: str
    nombre_corto: str
    color: str
    categoria: str
    orden: int
    descripcion: Optional[str]
    agentes: List[AgenteSimple]


class AgrupacionesListResponse(BaseModel):
    """Lista de agrupaciones."""

    items: List[AgrupacionListItem]
    total: int


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/", response_model=AgrupacionesListResponse)
def list_agrupaciones(
    categoria: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(RequireAnyRole()),
) -> AgrupacionesListResponse:
    """
    Lista todas las agrupaciones activas.

    Opcionalmente filtra por categoría funcional:
    - respiratorio
    - enterico
    - vectorial
    - etc.
    """
    stmt = (
        select(AgrupacionAgentes)
        .where(col(AgrupacionAgentes.activo).is_(True))
        .order_by(col(AgrupacionAgentes.orden))
    )

    if categoria:
        stmt = stmt.where(col(AgrupacionAgentes.categoria) == categoria)

    agrupaciones = session.exec(stmt).all()

    items = []
    for agrup in agrupaciones:
        # Contar agentes
        count_stmt = select(AgrupacionAgenteLink).where(
            col(AgrupacionAgenteLink.agrupacion_id) == agrup.id
        )
        count = len(session.exec(count_stmt).all())

        items.append(
            AgrupacionListItem(
                id=agrup.id,  # type: ignore[arg-type]
                slug=agrup.slug,
                nombre=agrup.nombre,
                nombre_corto=agrup.nombre_corto,
                color=agrup.color,
                categoria=agrup.categoria,
                orden=agrup.orden,
                agentes_count=count,
            )
        )

    return AgrupacionesListResponse(items=items, total=len(items))


@router.get("/{slug}", response_model=AgrupacionDetailResponse)
def get_agrupacion(
    slug: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(RequireAnyRole()),
) -> AgrupacionDetailResponse:
    """
    Obtiene detalle de una agrupación con sus agentes.

    Útil para drill-down: ver qué agentes componen una agrupación.
    """
    stmt = select(AgrupacionAgentes).where(
        col(AgrupacionAgentes.slug) == slug,
        col(AgrupacionAgentes.activo).is_(True),
    )
    agrupacion = session.exec(stmt).first()

    if not agrupacion:
        raise HTTPException(
            status_code=404, detail=f"Agrupación '{slug}' no encontrada"
        )

    # Obtener agentes
    agentes_stmt = (
        select(AgenteEtiologico)
        .join(
            AgrupacionAgenteLink,
            col(AgrupacionAgenteLink.agente_id) == col(AgenteEtiologico.id),
        )
        .where(col(AgrupacionAgenteLink.agrupacion_id) == agrupacion.id)
        .order_by(col(AgenteEtiologico.nombre))
    )
    agentes = session.exec(agentes_stmt).all()

    return AgrupacionDetailResponse(
        id=agrupacion.id,  # type: ignore[arg-type]
        slug=agrupacion.slug,
        nombre=agrupacion.nombre,
        nombre_corto=agrupacion.nombre_corto,
        color=agrupacion.color,
        categoria=agrupacion.categoria,
        orden=agrupacion.orden,
        descripcion=agrupacion.descripcion,
        agentes=[
            AgenteSimple(
                id=a.id,  # type: ignore[arg-type]
                slug=a.slug,
                nombre=a.nombre,
                nombre_corto=a.nombre_corto,
            )
            for a in agentes
        ],
    )


@router.get("/{slug}/agente-ids")
def get_agrupacion_agente_ids(
    slug: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(RequireAnyRole()),
) -> dict:
    """
    Obtiene solo los IDs de agentes de una agrupación.

    Optimizado para el sistema de métricas que necesita resolver
    una agrupación a sus IDs de agentes para filtrar.
    """
    from app.domains.catalogos.agentes.seed_agrupaciones import (
        get_agente_ids_for_agrupacion,
    )

    ids = get_agente_ids_for_agrupacion(session, slug)

    if not ids:
        raise HTTPException(
            status_code=404, detail=f"Agrupación '{slug}' no encontrada o sin agentes"
        )

    return {"slug": slug, "agente_ids": ids}
