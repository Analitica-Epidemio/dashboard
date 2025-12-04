"""
API endpoints para configuración de template de boletines
"""

import logging

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.boletines.schemas import (
    BoletinTemplateConfigResponse,
    CreateDynamicBlockRequest,
    UpdateDynamicBlockRequest,
    UpdateDynamicBlocksRequest,
    UpdateEventSectionTemplateRequest,
    UpdateStaticContentRequest,
)
from app.core.database import get_async_session
from app.core.schemas.response import SuccessResponse
from app.core.security import RequireAuthOrSignedUrl
from app.domains.autenticacion.models import User
from app.domains.boletines.models import BoletinTemplateConfig

logger = logging.getLogger(__name__)


async def get_template_config(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = RequireAuthOrSignedUrl,
) -> SuccessResponse[BoletinTemplateConfigResponse]:
    """
    Obtener configuración actual del template de boletines (singleton id=1)
    """
    result = await db.execute(
        select(BoletinTemplateConfig).where(BoletinTemplateConfig.id == 1)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=404,
            detail="No se encontró configuración de template. Ejecute el seed primero."
        )

    return SuccessResponse(
        data=BoletinTemplateConfigResponse(
            id=config.id,
            static_content_template=config.static_content_template,
            event_section_template=config.event_section_template or {},
            updated_at=config.updated_at,
            updated_by=config.updated_by,
        )
    )


async def update_static_content(
    request: UpdateStaticContentRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = RequireAuthOrSignedUrl,
) -> SuccessResponse[BoletinTemplateConfigResponse]:
    """
    Actualizar contenido estático del template
    """
    result = await db.execute(
        select(BoletinTemplateConfig).where(BoletinTemplateConfig.id == 1)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=404,
            detail="No se encontró configuración de template"
        )

    config.static_content_template = request.content
    config.updated_by = current_user.id

    await db.commit()
    await db.refresh(config)

    logger.info(
        f"Contenido estático actualizado por user_id={current_user.id}"
    )

    return SuccessResponse(
        data=BoletinTemplateConfigResponse(
            id=config.id,
            static_content_template=config.static_content_template,
            event_section_template=config.event_section_template or {},
            updated_at=config.updated_at,
            updated_by=config.updated_by,
        ),
        message="Contenido estático actualizado correctamente"
    )


async def update_event_section_template(
    request: UpdateEventSectionTemplateRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = RequireAuthOrSignedUrl,
) -> SuccessResponse[BoletinTemplateConfigResponse]:
    """
    Actualizar template de sección de evento (se repite por cada evento seleccionado)
    """
    result = await db.execute(
        select(BoletinTemplateConfig).where(BoletinTemplateConfig.id == 1)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=404,
            detail="No se encontró configuración de template"
        )

    config.event_section_template = request.content
    config.updated_by = current_user.id

    await db.commit()
    await db.refresh(config)

    logger.info(
        f"Template de sección de evento actualizado por user_id={current_user.id}"
    )

    return SuccessResponse(
        data=BoletinTemplateConfigResponse(
            id=config.id,
            static_content_template=config.static_content_template,
            event_section_template=config.event_section_template or {},
            updated_at=config.updated_at,
            updated_by=config.updated_by,
        ),
        message="Template de sección de evento actualizado correctamente"
    )


async def update_dynamic_blocks(
    request: UpdateDynamicBlocksRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = RequireAuthOrSignedUrl,
) -> SuccessResponse[BoletinTemplateConfigResponse]:
    """
    Actualizar array completo de bloques dinámicos (para reordenar)
    """
    result = await db.execute(
        select(BoletinTemplateConfig).where(BoletinTemplateConfig.id == 1)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=404,
            detail="No se encontró configuración de template"
        )

    # Validar que todos los bloques tengan los campos requeridos
    for block in request.blocks:
        if not all(k in block for k in ["id", "query_type", "render_type"]):
            raise HTTPException(
                status_code=400,
                detail="Bloque inválido: falta campos requeridos (id, query_type, render_type)"
            )

    config.dynamic_blocks_config = request.blocks
    config.updated_by = current_user.id

    await db.commit()
    await db.refresh(config)

    logger.info(
        f"Bloques dinámicos reordenados/actualizados por user_id={current_user.id}. "
        f"Total bloques: {len(request.blocks)}"
    )

    return SuccessResponse(
        data=BoletinTemplateConfigResponse(
            id=config.id,
            static_content_template=config.static_content_template,
            event_section_template=config.event_section_template or {},
            updated_at=config.updated_at,
            updated_by=config.updated_by,
        ),
        message="Bloques dinámicos actualizados correctamente"
    )


async def create_dynamic_block(
    request: CreateDynamicBlockRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = RequireAuthOrSignedUrl,
) -> SuccessResponse[BoletinTemplateConfigResponse]:
    """
    Agregar un nuevo bloque dinámico al final del array
    """
    result = await db.execute(
        select(BoletinTemplateConfig).where(BoletinTemplateConfig.id == 1)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=404,
            detail="No se encontró configuración de template"
        )

    # Verificar que el ID del bloque no exista
    existing_ids = [block["id"] for block in config.dynamic_blocks_config]
    if request.block["id"] in existing_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe un bloque con id '{request.block['id']}'"
        )

    # Agregar al final
    config.dynamic_blocks_config.append(request.block)
    config.updated_by = current_user.id

    # Forzar actualización del campo JSON
    db.add(config)
    await db.commit()
    await db.refresh(config)

    logger.info(
        f"Bloque dinámico '{request.block['id']}' creado por user_id={current_user.id}"
    )

    return SuccessResponse(
        data=BoletinTemplateConfigResponse(
            id=config.id,
            static_content_template=config.static_content_template,
            event_section_template=config.event_section_template or {},
            updated_at=config.updated_at,
            updated_by=config.updated_by,
        ),
        message=f"Bloque '{request.block['id']}' creado correctamente"
    )


async def update_dynamic_block(
    block_id: str,
    request: UpdateDynamicBlockRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = RequireAuthOrSignedUrl,
) -> SuccessResponse[BoletinTemplateConfigResponse]:
    """
    Actualizar configuración de un bloque específico
    """
    result = await db.execute(
        select(BoletinTemplateConfig).where(BoletinTemplateConfig.id == 1)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=404,
            detail="No se encontró configuración de template"
        )

    # Buscar el bloque
    block_index = None
    for i, block in enumerate(config.dynamic_blocks_config):
        if block["id"] == block_id:
            block_index = i
            break

    if block_index is None:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró bloque con id '{block_id}'"
        )

    # Actualizar el bloque
    config.dynamic_blocks_config[block_index] = request.block
    config.updated_by = current_user.id

    # Forzar actualización del campo JSON
    db.add(config)
    await db.commit()
    await db.refresh(config)

    logger.info(
        f"Bloque dinámico '{block_id}' actualizado por user_id={current_user.id}"
    )

    return SuccessResponse(
        data=BoletinTemplateConfigResponse(
            id=config.id,
            static_content_template=config.static_content_template,
            event_section_template=config.event_section_template or {},
            updated_at=config.updated_at,
            updated_by=config.updated_by,
        ),
        message=f"Bloque '{block_id}' actualizado correctamente"
    )


async def delete_dynamic_block(
    block_id: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = RequireAuthOrSignedUrl,
) -> SuccessResponse[BoletinTemplateConfigResponse]:
    """
    Eliminar un bloque dinámico
    """
    result = await db.execute(
        select(BoletinTemplateConfig).where(BoletinTemplateConfig.id == 1)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=404,
            detail="No se encontró configuración de template"
        )

    # Buscar y eliminar el bloque
    original_length = len(config.dynamic_blocks_config)
    config.dynamic_blocks_config = [
        block for block in config.dynamic_blocks_config
        if block["id"] != block_id
    ]

    if len(config.dynamic_blocks_config) == original_length:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró bloque con id '{block_id}'"
        )

    config.updated_by = current_user.id

    # Forzar actualización del campo JSON
    db.add(config)
    await db.commit()
    await db.refresh(config)

    logger.info(
        f"Bloque dinámico '{block_id}' eliminado por user_id={current_user.id}"
    )

    return SuccessResponse(
        data=BoletinTemplateConfigResponse(
            id=config.id,
            static_content_template=config.static_content_template,
            event_section_template=config.event_section_template or {},
            updated_at=config.updated_at,
            updated_by=config.updated_by,
        ),
        message=f"Bloque '{block_id}' eliminado correctamente"
    )
