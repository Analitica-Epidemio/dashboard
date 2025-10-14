"""
List grupos ENO endpoint
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_async_session
from app.core.schemas.response import PaginatedResponse
from app.core.security import RequireAnyRole
from app.domains.autenticacion.models import User
from app.domains.eventos_epidemiologicos.eventos.models import (
    GrupoEno,
    TipoEno,
    TipoEnoGrupoEno,
)


class TipoEnoSimple(BaseModel):
    id: int = Field(..., description="ID del tipo ENO")
    nombre: str = Field(..., max_length=200, description="Nombre del tipo ENO")


class GrupoEnoInfo(BaseModel):
    id: int = Field(..., description="ID del grupo ENO")
    nombre: str = Field(..., max_length=150, description="Nombre del grupo ENO")
    descripcion: Optional[str] = Field(
        None, max_length=500, description="Descripción del grupo"
    )
    codigo: Optional[str] = Field(None, max_length=200, description="Código del grupo")
    eventos: list[TipoEnoSimple] = Field(
        default_factory=list, description="Eventos (tipos ENO) que pertenecen a este grupo"
    )


logger = logging.getLogger(__name__)


async def list_grupos_eno(
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(20, ge=1, le=100, description="Elementos por página"),
    nombre: Optional[str] = Query(None, description="Filtrar por nombre"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(RequireAnyRole()),
) -> PaginatedResponse[GrupoEnoInfo]:
    try:
        # Construir query base - cargar eventos relacionados
        query = (
            select(GrupoEno)
            .distinct()
            .options(
                selectinload(GrupoEno.grupo_tipos).selectinload(TipoEnoGrupoEno.tipo_eno)
            )
        )

        # Aplicar filtros - buscar en nombre de grupo O en eventos que pertenecen al grupo
        if nombre:
            # Subquery para encontrar grupos que tienen eventos con el nombre buscado
            subquery_eventos = (
                select(TipoEnoGrupoEno.id_grupo_eno)
                .join(TipoEno, TipoEnoGrupoEno.id_tipo_eno == TipoEno.id)
                .where(TipoEno.nombre.ilike(f"%{nombre}%"))
            )

            # Buscar grupos cuyo nombre coincida O que tengan eventos que coincidan
            query = query.where(
                or_(
                    GrupoEno.nombre.ilike(f"%{nombre}%"),
                    GrupoEno.id.in_(subquery_eventos)
                )
            )

        # Contar total de elementos (usar la misma lógica de filtrado)
        count_query = select(func.count(func.distinct(GrupoEno.id))).select_from(GrupoEno)
        if nombre:
            subquery_eventos = (
                select(TipoEnoGrupoEno.id_grupo_eno)
                .join(TipoEno, TipoEnoGrupoEno.id_tipo_eno == TipoEno.id)
                .where(TipoEno.nombre.ilike(f"%{nombre}%"))
            )
            count_query = count_query.where(
                or_(
                    GrupoEno.nombre.ilike(f"%{nombre}%"),
                    GrupoEno.id.in_(subquery_eventos)
                )
            )

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Aplicar paginación
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        # Ejecutar query
        result = await db.execute(query)
        grupos = result.scalars().all()

        # Convertir a modelo de respuesta
        grupos_info = [
            GrupoEnoInfo(
                id=grupo.id,
                nombre=grupo.nombre,
                descripcion=grupo.descripcion,
                codigo=grupo.codigo,
                eventos=[
                    TipoEnoSimple(id=rel.tipo_eno.id, nombre=rel.tipo_eno.nombre)
                    for rel in grupo.grupo_tipos
                ],
            )
            for grupo in grupos
        ]

        # Calcular páginas totales
        total_pages = (total + per_page - 1) // per_page if total > 0 else 0

        return PaginatedResponse(
            data=grupos_info,
            meta={
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
            },
            links={
                "first": (
                    f"/api/v1/gruposEno?page=1&per_page={per_page}"
                    if total_pages > 0
                    else None
                ),
                "prev": (
                    f"/api/v1/gruposEno?page={page-1}&per_page={per_page}"
                    if page > 1
                    else None
                ),
                "next": (
                    f"/api/v1/gruposEno?page={page+1}&per_page={per_page}"
                    if page < total_pages
                    else None
                ),
                "last": (
                    f"/api/v1/gruposEno?page={total_pages}&per_page={per_page}"
                    if total_pages > 0
                    else None
                ),
            },
        )
    except Exception as e:
        logger.error(f"💥 Error listando grupos ENO: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo grupos de eventos: {str(e)}",
        )
