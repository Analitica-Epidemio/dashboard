"""
List tipos ENO endpoint
"""

import logging
from typing import List, Optional

from fastapi import Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_async_session
from app.core.schemas.response import PaginatedResponse, PaginationMeta
from app.core.security import RequireAnyRole
from app.domains.autenticacion.models import User
from app.domains.eventos_epidemiologicos.eventos.models import (
    TipoEno,
    TipoEnoGrupoEno,
)


class GrupoInfo(BaseModel):
    """Información de un grupo"""
    id: int
    nombre: str


class TipoEnoInfo(BaseModel):
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

logger = logging.getLogger(__name__)


async def list_tipos_eno(
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(20, ge=1, le=100, description="Elementos por página"),
    nombre: Optional[str] = Query(None, description="Filtrar por nombre del tipo"),
    grupo_id: Optional[int] = Query(None, description="Filtrar por ID del grupo"),
    grupos: Optional[List[int]] = Query(None, description="Filtrar por múltiples IDs de grupo"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(RequireAnyRole()),
) -> PaginatedResponse[TipoEnoInfo]:
    try:
        # Construir query base
        query = select(TipoEno).options(
            selectinload(TipoEno.tipo_grupos).selectinload(TipoEnoGrupoEno.grupo_eno)
        )

        # Aplicar filtros
        if nombre:
            query = query.where(TipoEno.nombre.ilike(f"%{nombre}%"))

        # Filtrar por grupo usando subquery en la tabla de unión
        if grupo_id:
            query = query.where(
                TipoEno.id.in_(
                    select(TipoEnoGrupoEno.id_tipo_eno).where(
                        TipoEnoGrupoEno.id_grupo_eno == grupo_id
                    )
                )
            )
        elif grupos:
            query = query.where(
                TipoEno.id.in_(
                    select(TipoEnoGrupoEno.id_tipo_eno).where(
                        TipoEnoGrupoEno.id_grupo_eno.in_(grupos)
                    )
                )
            )

        # Contar total de elementos con los mismos filtros
        count_query = select(func.count(TipoEno.id.distinct()))
        if nombre:
            count_query = count_query.where(TipoEno.nombre.ilike(f"%{nombre}%"))
        if grupo_id:
            count_query = count_query.where(
                TipoEno.id.in_(
                    select(TipoEnoGrupoEno.id_tipo_eno).where(
                        TipoEnoGrupoEno.id_grupo_eno == grupo_id
                    )
                )
            )
        elif grupos:
            count_query = count_query.where(
                TipoEno.id.in_(
                    select(TipoEnoGrupoEno.id_tipo_eno).where(
                        TipoEnoGrupoEno.id_grupo_eno.in_(grupos)
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
        tipos = result.scalars().all()

        # Convertir a modelo de respuesta
        tipos_info = []
        for tipo in tipos:
            # Extraer grupos desde la relación many-to-many
            grupos_list = []
            if hasattr(tipo, 'tipo_grupos') and tipo.tipo_grupos:
                grupos_list = [
                    GrupoInfo(id=tg.grupo_eno.id, nombre=tg.grupo_eno.nombre)
                    for tg in tipo.tipo_grupos
                    if tg.grupo_eno
                ]

            tipos_info.append(
                TipoEnoInfo(
                    id=tipo.id,
                    nombre=tipo.nombre,
                    descripcion=tipo.descripcion,
                    codigo=tipo.codigo,
                    grupos=grupos_list
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
