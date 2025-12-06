"""
List tipos ENO endpoint con estadísticas
"""

import logging
from typing import List, Optional

from fastapi import Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_async_session
from app.core.schemas.response import PaginatedResponse, PaginationMeta
from app.core.security import RequireAnyRole
from app.domains.autenticacion.models import User
from app.domains.vigilancia_nominal.models.enfermedad import (
    Enfermedad,
    EnfermedadGrupo,
)
from app.domains.vigilancia_nominal.models.caso import CasoEpidemiologico


class GrupoInfo(BaseModel):
    """Información de un grupo"""
    id: int
    nombre: str


class EnfermedadInfo(BaseModel):
    id: int = Field(..., description="ID del tipo ENO")
    nombre: str = Field(..., max_length=200, description="Nombre del tipo ENO")
    descripcion: Optional[str] = Field(
        None, max_length=500, description="Descripción del tipo"
    )
    codigo: Optional[str] = Field(
        None, description="Código del tipo"
    )
    grupos: List[GrupoInfo] = Field(
        default_factory=list, description="Lista de grupos a los que pertenece este tipo"
    )
    # Estadísticas
    total_casos: int = Field(0, description="Total de casos registrados")


logger = logging.getLogger(__name__)


async def list_tipos_eno(
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(50, ge=1, le=200, description="Elementos por página"),
    nombre: Optional[str] = Query(None, description="Filtrar por nombre del tipo"),
    grupo_id: Optional[int] = Query(None, description="Filtrar por ID del grupo"),
    grupos: Optional[List[int]] = Query(None, description="Filtrar por múltiples IDs de grupo"),
    ordenar_por: str = Query(
        "total_casos",
        description="Campo para ordenar: nombre, codigo, total_casos"
    ),
    orden: str = Query("desc", description="Orden: asc o desc"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(RequireAnyRole()),
) -> PaginatedResponse[EnfermedadInfo]:
    try:
        # Subquery para contar casos por tipo_eno
        casos_subquery = (
            select(
                CasoEpidemiologico.id_enfermedad,
                func.count(CasoEpidemiologico.id).label("total_casos")
            )
            .group_by(CasoEpidemiologico.id_enfermedad)
            .subquery()
        )

        # Query principal
        query = (
            select(
                Enfermedad,
                func.coalesce(casos_subquery.c.total_casos, 0).label("total_casos")
            )
            .outerjoin(casos_subquery, Enfermedad.id == casos_subquery.c.id_enfermedad)
            .options(
                selectinload(Enfermedad.enfermedad_grupos).selectinload(EnfermedadGrupo.grupo)
            )
        )

        # Aplicar filtros
        if nombre:
            query = query.where(Enfermedad.nombre.ilike(f"%{nombre}%"))

        # Filtrar por grupo usando subquery en la tabla de unión
        if grupo_id:
            query = query.where(
                Enfermedad.id.in_(
                    select(EnfermedadGrupo.id_enfermedad).where(
                        EnfermedadGrupo.id_grupo == grupo_id
                    )
                )
            )
        elif grupos:
            query = query.where(
                Enfermedad.id.in_(
                    select(EnfermedadGrupo.id_enfermedad).where(
                        EnfermedadGrupo.id_grupo.in_(grupos)
                    )
                )
            )

        # Ordenamiento
        order_func = desc if orden.lower() == "desc" else asc
        if ordenar_por == "nombre":
            query = query.order_by(order_func(Enfermedad.nombre))
        elif ordenar_por == "slug":
            query = query.order_by(order_func(Enfermedad.slug))
        elif ordenar_por == "total_casos":
            query = query.order_by(order_func(func.coalesce(casos_subquery.c.total_casos, 0)))
        else:
            # Default: por total_casos descendente
            query = query.order_by(desc(func.coalesce(casos_subquery.c.total_casos, 0)))

        # Contar total de elementos con los mismos filtros
        count_query = select(func.count(Enfermedad.id.distinct()))
        if nombre:
            count_query = count_query.where(Enfermedad.nombre.ilike(f"%{nombre}%"))
        if grupo_id:
            count_query = count_query.where(
                Enfermedad.id.in_(
                    select(EnfermedadGrupo.id_enfermedad).where(
                        EnfermedadGrupo.id_grupo == grupo_id
                    )
                )
            )
        elif grupos:
            count_query = count_query.where(
                Enfermedad.id.in_(
                    select(EnfermedadGrupo.id_enfermedad).where(
                        EnfermedadGrupo.id_grupo.in_(grupos)
                    )
                )
            )

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Aplicar paginación
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        # Ejecutar query
        result = await db.execute(query)
        rows = result.all()

        # Convertir a modelo de respuesta
        tipos_info = []
        for row in rows:
            tipo = row[0]
            total_casos = row[1] or 0

            # Extraer grupos desde la relación many-to-many
            grupos_list = []
            if hasattr(tipo, 'tipo_grupos') and tipo.enfermedad_grupos:
                grupos_list = [
                    GrupoInfo(id=tg.grupo.id, nombre=tg.grupo.nombre)
                    for tg in tipo.enfermedad_grupos
                    if tg.grupo
                ]

            tipos_info.append(
                EnfermedadInfo(
                    id=tipo.id,
                    nombre=tipo.nombre,
                    descripcion=tipo.descripcion,
                    codigo=tipo.slug,
                    grupos=grupos_list,
                    total_casos=total_casos,
                )
            )

        # Calcular páginas totales
        total_pages = (total + per_page - 1) // per_page if total > 0 else 0

        return PaginatedResponse(
            data=tipos_info,
            meta=PaginationMeta(
                page=page,
                page_size=per_page,
                total=total,
                total_pages=total_pages,
            ),
            links={
                "first": f"/api/v1/tiposEno?page=1&per_page={per_page}" if total_pages > 0 else None,
                "prev": f"/api/v1/tiposEno?page={page-1}&per_page={per_page}" if page > 1 else None,
                "next": f"/api/v1/tiposEno?page={page+1}&per_page={per_page}" if page < total_pages else None,
                "last": f"/api/v1/tiposEno?page={total_pages}&per_page={per_page}" if total_pages > 0 else None
            }
        )
    except Exception as e:
        logger.error(f"💥 Error listando tipos ENO: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo tipos de eventos: {str(e)}",
        )
