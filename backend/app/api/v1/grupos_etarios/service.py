import logging
from typing import Optional, Any

from fastapi import Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.schemas.response import SuccessResponse
from .schemas import ConfiguracionRangosCreate, ConfiguracionRangosOut
from app.core.database import get_async_session
from app.core.security import RequireAnyRole
from app.core.schemas.response import PaginatedResponse
from app.domains.autenticacion.models import User
from app.domains.grupos_etarios.gruposetarios_models import ConfiguracionRangos

logger = logging.getLogger(__name__)


# ======================
# SCHEMA DE RESPUESTA
# ======================
class ConfiguracionRangosInfo(BaseModel):
    id: int = Field(..., description="ID de la configuración")
    nombre: str = Field(..., description="Nombre del grupo etario")
    rangos: Any = Field(..., description="Lista de rangos (JSON)")


# ======================
# ENDPOINT LIST
# ======================
async def list_configuracion_rangos(
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(20, ge=1, le=100, description="Elementos por página"),
    nombre: Optional[str] = Query(None, description="Filtrar por nombre"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(RequireAnyRole()),
) -> PaginatedResponse[ConfiguracionRangosInfo]:

    try:
        # ========== QUERY BASE ==========
        query = select(ConfiguracionRangos)

        # ========== FILTRO ==========
        if nombre:
            query = query.where(ConfiguracionRangos.nombre.ilike(f"%{nombre}%"))

        # ========== COUNT ==========
        count_query = select(func.count(ConfiguracionRangos.id))
        if nombre:
            count_query = count_query.where(ConfiguracionRangos.nombre.ilike(f"%{nombre}%"))

        total = (await db.execute(count_query)).scalar() or 0

        # ========== PAGINACIÓN ==========
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        result = await db.execute(query)
        configuraciones = result.scalars().all()

        # ========== ARMAR RESPUESTA ==========
        items = [
            ConfiguracionRangosInfo(
                id=c.id,
                nombre=c.nombre,
                rangos=c.rangos,
            )
            for c in configuraciones
        ]

        total_pages = (total + per_page - 1) // per_page if total > 0 else 0

        return PaginatedResponse(
            data=items,
            meta={
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
            },
            links={
                "first": f"/api/v1/configuracionRangos?page=1&per_page={per_page}",
                "prev": f"/api/v1/configuracionRangos?page={page-1}&per_page={per_page}" if page > 1 else None,
                "next": f"/api/v1/configuracionRangos?page={page+1}&per_page={per_page}" if page < total_pages else None,
                "last": f"/api/v1/configuracionRangos?page={total_pages}&per_page={per_page}",
            },
        )

    except Exception as e:
        logger.error(f"Error listando configuraciones de rangos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo configuraciones de rangos: {str(e)}",
        )

async def create_configuracion_rangos(
    data: ConfiguracionRangosCreate,
    db: AsyncSession,
    current_user: User
) -> ConfiguracionRangosOut:  # o SuccessResponse
    try:
        nuevo = ConfiguracionRangos(
            nombre=data.nombre,
            rangos=[r.dict() for r in data.rangos],
        )

        db.add(nuevo)
        await db.commit()
        await db.refresh(nuevo)

        return ConfiguracionRangosOut(
            id=nuevo.id,
            nombre=nuevo.nombre,
            descripcion=data.descripcion,
            rangos=nuevo.rangos,
        )

    except Exception as e:
        logger.error(f"Error creando configuración de rangos: {str(e)}")
        raise HTTPException(500, f"No se pudo crear la configuración: {str(e)}")



async def delete_configuracion_rangos(
    id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(RequireAnyRole()),
) -> SuccessResponse[bool]:

    try:
        result = await db.execute(select(ConfiguracionRangos).where(ConfiguracionRangos.id == id))
        config = result.scalar_one_or_none()

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Configuración no encontrada",
            )

        await db.delete(config)
        await db.commit()

        return SuccessResponse(
            data=True,
            message="Configuración eliminada correctamente",
        )

    except Exception as e:
        logger.error(f"Error eliminando configuración: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudo eliminar la configuración: {str(e)}",
        )





