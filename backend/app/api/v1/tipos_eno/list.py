"""
List tipos ENO endpoint
"""

import logging
from typing import List, Optional
from fastapi import Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.database import get_async_session
from app.core.schemas.response import PaginatedResponse
from app.core.security import RequireAnyRole
from app.domains.auth.models import User
from app.domains.eventos.models import TipoEno
from pydantic import BaseModel, Field
from typing import Optional


class TipoEnoInfo(BaseModel):
    id: int = Field(..., description="ID del tipo ENO")
    nombre: str = Field(..., max_length=200, description="Nombre del tipo ENO")
    descripcion: Optional[str] = Field(
        None, max_length=500, description="Descripción del tipo"
    )
    codigo: Optional[str] = Field(
        None, description="Código del tipo"
    )
    id_grupo_eno: int = Field(
        ..., description="ID del grupo ENO"
    )
    grupo_nombre: Optional[str] = Field(
        None, description="Nombre del grupo ENO"
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
        # Construir query base con join para obtener el nombre del grupo
        query = select(TipoEno).options(selectinload(TipoEno.grupo_eno))

        # Aplicar filtros
        if nombre:
            query = query.where(TipoEno.nombre.ilike(f"%{nombre}%"))
        if grupo_id:
            query = query.where(TipoEno.id_grupo_eno == grupo_id)
        if grupos:
            query = query.where(TipoEno.id_grupo_eno.in_(grupos))

        # Contar total de elementos
        count_query = select(func.count()).select_from(TipoEno)
        if nombre:
            count_query = count_query.where(TipoEno.nombre.ilike(f"%{nombre}%"))
        if grupo_id:
            count_query = count_query.where(TipoEno.id_grupo_eno == grupo_id)
        if grupos:
            count_query = count_query.where(TipoEno.id_grupo_eno.in_(grupos))

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Aplicar paginación
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        # Ejecutar query
        result = await db.execute(query)
        tipos = result.scalars().all()

        # Convertir a modelo de respuesta
        tipos_info = [
            TipoEnoInfo(
                id=tipo.id,
                nombre=tipo.nombre,
                descripcion=tipo.descripcion,
                codigo=tipo.codigo,
                id_grupo_eno=tipo.id_grupo_eno,
                grupo_nombre=tipo.grupo_eno.nombre if tipo.grupo_eno else None
            )
            for tipo in tipos
        ]

        # Calcular páginas totales
        total_pages = (total + per_page - 1) // per_page if total > 0 else 0

        return PaginatedResponse(
            data=tipos_info,
            meta={
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages
            },
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