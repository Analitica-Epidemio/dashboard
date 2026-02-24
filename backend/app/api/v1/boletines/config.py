"""
API endpoints para configuración de template de boletines
"""

import logging

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from app.api.v1.boletines.schemas import (
    BoletinTemplateConfigResponse,
    UpdateEventSectionTemplateRequest,
    UpdateMetadataRequest,
    UpdateSeccionesOrderRequest,
    UpdateStaticContentRequest,
)
from app.core.database import get_async_session
from app.core.schemas.response import SuccessResponse
from app.core.security import RequireAuthOrSignedUrl
from app.domains.autenticacion.models import User
from app.domains.boletines.models import BoletinSeccion, BoletinTemplateConfig

logger = logging.getLogger(__name__)


def _config_to_response(config: BoletinTemplateConfig) -> BoletinTemplateConfigResponse:
    """Helper para convertir modelo a response."""
    assert config.id is not None
    return BoletinTemplateConfigResponse(
        id=config.id,
        static_content_template=config.static_content_template,
        event_section_template=config.event_section_template or {},
        boletin_metadata=config.boletin_metadata or {},
        updated_at=config.updated_at,
        updated_by=config.updated_by,
    )


async def _get_config_or_404(
    db: AsyncSession,
) -> BoletinTemplateConfig:
    """Helper para obtener el singleton o lanzar 404."""
    result = await db.execute(
        select(BoletinTemplateConfig).where(col(BoletinTemplateConfig.id) == 1)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=404,
            detail="No se encontró configuración de template. Ejecute el seed primero.",
        )

    if config.id is None:
        raise HTTPException(status_code=500, detail="Configuración de template sin ID")

    return config


async def get_template_config(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = RequireAuthOrSignedUrl,
) -> SuccessResponse[BoletinTemplateConfigResponse]:
    """
    Obtener configuración actual del template de boletines (singleton id=1)
    """
    config = await _get_config_or_404(db)
    return SuccessResponse(data=_config_to_response(config))


async def update_static_content(
    request: UpdateStaticContentRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = RequireAuthOrSignedUrl,
) -> SuccessResponse[BoletinTemplateConfigResponse]:
    """
    Actualizar contenido estático del template
    """
    config = await _get_config_or_404(db)

    config.static_content_template = request.content
    config.updated_by = current_user.id

    await db.commit()
    await db.refresh(config)

    logger.info(f"Contenido estático actualizado por user_id={current_user.id}")

    return SuccessResponse(data=_config_to_response(config))


async def update_event_section_template(
    request: UpdateEventSectionTemplateRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = RequireAuthOrSignedUrl,
) -> SuccessResponse[BoletinTemplateConfigResponse]:
    """
    Actualizar template de sección de evento (se repite por cada evento seleccionado)
    """
    config = await _get_config_or_404(db)

    config.event_section_template = request.content
    config.updated_by = current_user.id

    await db.commit()
    await db.refresh(config)

    logger.info(
        f"Template de sección de evento actualizado por user_id={current_user.id}"
    )

    return SuccessResponse(data=_config_to_response(config))


async def update_metadata(
    request: UpdateMetadataRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = RequireAuthOrSignedUrl,
) -> SuccessResponse[BoletinTemplateConfigResponse]:
    """
    Actualizar metadatos del boletín (institución, autoridades, logo, etc.)
    """
    config = await _get_config_or_404(db)

    config.boletin_metadata = request.boletin_metadata
    config.updated_by = current_user.id

    await db.commit()
    await db.refresh(config)

    logger.info(f"Metadatos del boletín actualizados por user_id={current_user.id}")

    return SuccessResponse(data=_config_to_response(config))


async def update_secciones_order(
    request: UpdateSeccionesOrderRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = RequireAuthOrSignedUrl,
) -> SuccessResponse[dict]:
    """
    Actualizar orden y estado activo de las secciones del boletín.
    """
    for item in request.secciones:
        result = await db.execute(
            select(BoletinSeccion).where(col(BoletinSeccion.id) == item.id)
        )
        seccion = result.scalar_one_or_none()
        if seccion:
            seccion.orden = item.orden
            seccion.activo = item.activo

    await db.commit()

    logger.info(
        f"Orden de secciones actualizado por user_id={current_user.id} "
        f"({len(request.secciones)} secciones)"
    )

    return SuccessResponse(data={"updated": len(request.secciones)})
