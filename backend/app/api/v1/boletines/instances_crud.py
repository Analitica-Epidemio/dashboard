"""
CRUD operations para instancias de boletines (boletines generados)
"""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.boletines.schemas import (
    BoletinGenerateRequest,
    BoletinInstanceResponse,
)
from app.core.database import get_async_session
from app.core.schemas.response import SuccessResponse
from app.core.security import RequireAuthOrSignedUrl
from app.domains.autenticacion.models import User
from app.domains.boletines.models import BoletinInstance, BoletinTemplate

logger = logging.getLogger(__name__)


async def create_instance(
    request_data: BoletinGenerateRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = RequireAuthOrSignedUrl,
) -> SuccessResponse[BoletinInstanceResponse]:
    """
    Crear una nueva instancia de boletín (sin generar PDF todavía).
    El PDF se generará en un paso posterior.
    """
    # Verificar que el template existe
    stmt = select(BoletinTemplate).where(BoletinTemplate.id == request_data.template_id)
    result = await db.execute(stmt)
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template no encontrado")

    # Crear instancia
    instance = BoletinInstance(
        template_id=request_data.template_id,
        name=request_data.name,
        parameters=request_data.parameters,
        status="pending",
        generated_by=current_user.id if current_user else None,
    )

    db.add(instance)
    await db.commit()
    await db.refresh(instance)

    logger.info(f"Instancia creada: {instance.name} (ID: {instance.id})")

    return SuccessResponse(data=BoletinInstanceResponse.model_validate(instance))


async def list_instances(
    template_id: Optional[int] = Query(None, description="Filtrar por template"),
    status: Optional[str] = Query(None, description="Filtrar por estado"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = RequireAuthOrSignedUrl,
) -> SuccessResponse[List[BoletinInstanceResponse]]:
    """
    Listar instancias de boletines generados.
    """
    stmt = select(BoletinInstance).order_by(BoletinInstance.created_at.desc())

    # Filtros
    if template_id:
        stmt = stmt.where(BoletinInstance.template_id == template_id)

    if status:
        stmt = stmt.where(BoletinInstance.status == status)

    # Si no es admin, solo mostrar propias instancias
    if current_user and not getattr(current_user, 'is_admin', False):
        stmt = stmt.where(BoletinInstance.generated_by == current_user.id)

    # Paginación
    stmt = stmt.offset(offset).limit(limit)

    result = await db.execute(stmt)
    instances = result.scalars().all()

    return SuccessResponse(
        data=[BoletinInstanceResponse.model_validate(i) for i in instances]
    )


async def get_instance(
    instance_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = RequireAuthOrSignedUrl,
) -> SuccessResponse[BoletinInstanceResponse]:
    """
    Obtener una instancia específica por ID.
    """
    stmt = select(BoletinInstance).where(BoletinInstance.id == instance_id)
    result = await db.execute(stmt)
    instance = result.scalar_one_or_none()

    if not instance:
        raise HTTPException(status_code=404, detail="Instancia no encontrada")

    # Verificar permisos
    if not current_user or (instance.generated_by != current_user.id and not getattr(current_user, 'is_admin', False)):
        raise HTTPException(status_code=403, detail="No tiene permisos para ver esta instancia")

    return SuccessResponse(data=BoletinInstanceResponse.model_validate(instance))


async def delete_instance(
    instance_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = RequireAuthOrSignedUrl,
) -> SuccessResponse[dict]:
    """
    Eliminar una instancia.
    """
    stmt = select(BoletinInstance).where(BoletinInstance.id == instance_id)
    result = await db.execute(stmt)
    instance = result.scalar_one_or_none()

    if not instance:
        raise HTTPException(status_code=404, detail="Instancia no encontrada")

    # Verificar permisos
    if not current_user or (instance.generated_by != current_user.id and not getattr(current_user, 'is_admin', False)):
        raise HTTPException(status_code=403, detail="No tiene permisos para eliminar esta instancia")

    # TODO: Eliminar archivo PDF si existe
    # if instance.pdf_path and os.path.exists(instance.pdf_path):
    #     os.remove(instance.pdf_path)

    await db.delete(instance)
    await db.commit()

    logger.info(f"Instancia eliminada: {instance.name} (ID: {instance.id})")

    return SuccessResponse(data={"message": "Instancia eliminada exitosamente"})
