"""
CRUD operations para templates de boletines
"""

import logging
from typing import List, Optional

from fastapi import Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.boletines.schemas import (
    BoletinTemplateCreate,
    BoletinTemplateResponse,
    BoletinTemplateUpdate,
)
from app.core.database import get_async_session
from app.core.schemas.response import SuccessResponse
from app.core.security import RequireAuthOrSignedUrl
from app.domains.autenticacion.models import User
from app.domains.boletines.models import BoletinTemplate

logger = logging.getLogger(__name__)


async def create_template(
    template_data: BoletinTemplateCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = RequireAuthOrSignedUrl,
) -> SuccessResponse[BoletinTemplateResponse]:
    """
    Crear un nuevo template de boletín.
    """
    # Convertir Pydantic models a dict para JSON columns
    template = BoletinTemplate(
        name=template_data.name,
        description=template_data.description,
        category=template_data.category,
        thumbnail=template_data.thumbnail,
        layout=template_data.layout.model_dump(),
        cover=template_data.cover.model_dump() if template_data.cover else None,
        widgets=[w.model_dump() for w in template_data.widgets],
        global_filters=template_data.global_filters.model_dump() if template_data.global_filters else None,
        is_public=template_data.is_public,
        created_by=current_user.id if current_user else None,
    )

    db.add(template)
    await db.commit()
    await db.refresh(template)

    logger.info(f"Template creado: {template.name} (ID: {template.id})")

    return SuccessResponse(data=BoletinTemplateResponse.model_validate(template))


async def list_templates(
    category: Optional[str] = Query(None, description="Filtrar por categoría"),
    is_public: Optional[bool] = Query(None, description="Filtrar por público/privado"),
    search: Optional[str] = Query(None, description="Buscar por nombre o descripción"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = RequireAuthOrSignedUrl,
) -> SuccessResponse[List[BoletinTemplateResponse]]:
    """
    Listar templates de boletines con filtros opcionales.
    """
    stmt = select(BoletinTemplate)

    # Filtros
    if category:
        stmt = stmt.where(BoletinTemplate.category == category)

    if is_public is not None:
        stmt = stmt.where(BoletinTemplate.is_public == is_public)

    if search:
        search_pattern = f"%{search}%"
        stmt = stmt.where(
            (BoletinTemplate.name.ilike(search_pattern)) |
            (BoletinTemplate.description.ilike(search_pattern))
        )

    # Si no es admin, solo mostrar templates públicos o propios
    if current_user and not getattr(current_user, 'is_admin', False):
        stmt = stmt.where(
            (BoletinTemplate.is_public.is_(True)) |
            (BoletinTemplate.created_by == current_user.id)
        )

    # Paginación
    stmt = stmt.offset(offset).limit(limit)

    result = await db.execute(stmt)
    templates = result.scalars().all()

    return SuccessResponse(
        data=[BoletinTemplateResponse.model_validate(t) for t in templates]
    )


async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = RequireAuthOrSignedUrl,
) -> SuccessResponse[BoletinTemplateResponse]:
    """
    Obtener un template específico por ID.
    """
    stmt = select(BoletinTemplate).where(BoletinTemplate.id == template_id)
    result = await db.execute(stmt)
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template no encontrado")

    # Verificar permisos (solo si no es público y no es el creador)
    if not template.is_public:
        if not current_user or (template.created_by != current_user.id and not getattr(current_user, 'is_admin', False)):
            raise HTTPException(status_code=403, detail="No tiene permisos para ver este template")

    return SuccessResponse(data=BoletinTemplateResponse.model_validate(template))


async def update_template(
    template_id: int,
    template_data: BoletinTemplateUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = RequireAuthOrSignedUrl,
) -> SuccessResponse[BoletinTemplateResponse]:
    """
    Actualizar un template existente.
    """
    stmt = select(BoletinTemplate).where(BoletinTemplate.id == template_id)
    result = await db.execute(stmt)
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template no encontrado")

    # Verificar permisos
    if template.is_system:
        raise HTTPException(status_code=403, detail="No se pueden editar templates del sistema")

    if not current_user or (template.created_by != current_user.id and not getattr(current_user, 'is_admin', False)):
        raise HTTPException(status_code=403, detail="No tiene permisos para editar este template")

    # Actualizar campos
    update_data = template_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if value is not None:
            # Convertir Pydantic models a dict para JSON columns
            if field in ['layout', 'cover', 'global_filters'] and hasattr(value, 'model_dump'):
                value = value.model_dump()
            elif field == 'widgets' and isinstance(value, list):
                value = [w.model_dump() if hasattr(w, 'model_dump') else w for w in value]

            setattr(template, field, value)

    await db.commit()
    await db.refresh(template)

    logger.info(f"Template actualizado: {template.name} (ID: {template.id})")

    return SuccessResponse(data=BoletinTemplateResponse.model_validate(template))


async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = RequireAuthOrSignedUrl,
) -> SuccessResponse[dict]:
    """
    Eliminar un template.
    """
    stmt = select(BoletinTemplate).where(BoletinTemplate.id == template_id)
    result = await db.execute(stmt)
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template no encontrado")

    # Verificar permisos
    if template.is_system:
        raise HTTPException(status_code=403, detail="No se pueden eliminar templates del sistema")

    if not current_user or (template.created_by != current_user.id and not getattr(current_user, 'is_admin', False)):
        raise HTTPException(status_code=403, detail="No tiene permisos para eliminar este template")

    await db.delete(template)
    await db.commit()

    logger.info(f"Template eliminado: {template.name} (ID: {template.id})")

    return SuccessResponse(data={"message": "Template eliminado exitosamente"})


async def duplicate_template(
    template_id: int,
    new_name: str = Query(..., description="Nombre para el template duplicado"),
    db: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = RequireAuthOrSignedUrl,
) -> SuccessResponse[BoletinTemplateResponse]:
    """
    Duplicar un template existente.
    """
    # Obtener template original
    stmt = select(BoletinTemplate).where(BoletinTemplate.id == template_id)
    result = await db.execute(stmt)
    original = result.scalar_one_or_none()

    if not original:
        raise HTTPException(status_code=404, detail="Template no encontrado")

    # Verificar permisos de lectura
    if not original.is_public:
        if not current_user or (original.created_by != current_user.id and not getattr(current_user, 'is_admin', False)):
            raise HTTPException(status_code=403, detail="No tiene permisos para duplicar este template")

    # Crear copia
    duplicate = BoletinTemplate(
        name=new_name,
        description=f"Copia de: {original.description or original.name}",
        category=original.category,
        thumbnail=original.thumbnail,
        layout=original.layout,
        cover=original.cover,
        widgets=original.widgets,
        global_filters=original.global_filters,
        is_public=False,  # El duplicado es privado por defecto
        created_by=current_user.id if current_user else None,
    )

    db.add(duplicate)
    await db.commit()
    await db.refresh(duplicate)

    logger.info(f"Template duplicado: {original.name} -> {duplicate.name}")

    return SuccessResponse(data=BoletinTemplateResponse.model_validate(duplicate))
