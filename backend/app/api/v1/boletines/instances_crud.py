"""
CRUD operations para instancias de boletines (boletines generados)
"""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import Depends, HTTPException, Query
from pydantic import BaseModel
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
from app.features.boletines.html_renderer import BulletinHTMLRenderer

logger = logging.getLogger(__name__)


class UpdateInstanceContentRequest(BaseModel):
    """Request para actualizar el contenido HTML de una instancia"""
    content: str


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


async def update_instance_content(
    instance_id: int,
    request_data: UpdateInstanceContentRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = RequireAuthOrSignedUrl,
) -> SuccessResponse[BoletinInstanceResponse]:
    """
    Actualizar el contenido HTML de una instancia de boletín.
    """
    stmt = select(BoletinInstance).where(BoletinInstance.id == instance_id)
    result = await db.execute(stmt)
    instance = result.scalar_one_or_none()

    if not instance:
        raise HTTPException(status_code=404, detail="Instancia no encontrada")

    # Verificar permisos
    if not current_user or (instance.generated_by != current_user.id and not getattr(current_user, 'is_admin', False)):
        raise HTTPException(status_code=403, detail="No tiene permisos para editar esta instancia")

    # Actualizar contenido
    instance.content = request_data.content

    await db.commit()
    await db.refresh(instance)

    logger.info(f"Contenido actualizado para instancia: {instance.name} (ID: {instance.id})")

    return SuccessResponse(data=BoletinInstanceResponse.model_validate(instance))


async def generate_instance_pdf(
    instance_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = RequireAuthOrSignedUrl,
):
    """
    Generar PDF de una instancia de boletín y retornarlo como descarga.
    """
    from fastapi.responses import FileResponse
    import tempfile
    import os

    stmt = select(BoletinInstance).where(BoletinInstance.id == instance_id)
    result = await db.execute(stmt)
    instance = result.scalar_one_or_none()

    if not instance:
        raise HTTPException(status_code=404, detail="Instancia no encontrada")

    # Verificar permisos
    if not current_user or (instance.generated_by != current_user.id and not getattr(current_user, 'is_admin', False)):
        raise HTTPException(status_code=403, detail="No tiene permisos para generar PDF de esta instancia")

    if not instance.content:
        raise HTTPException(status_code=400, detail="La instancia no tiene contenido para generar PDF")

    try:
        # Renderizar el HTML con los gráficos convertidos a imágenes usando la misma sesión
        html_renderer = BulletinHTMLRenderer(db)
        rendered_html = await html_renderer.render_html_with_charts(instance.content)

        safe_name = (instance.name or f"boletin_{instance_id}").strip() or f"boletin_{instance_id}"

        # Crear archivo temporal para el PDF
        temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_pdf_path = temp_pdf.name
        temp_pdf.close()

        # Generar PDF usando el servicio serverside
        from app.features.reporteria.serverside_pdf_generator import ServerSidePDFGenerator

        pdf_generator = ServerSidePDFGenerator()
        await pdf_generator.generate_pdf_from_html(
            html_content=rendered_html,
            output_path=temp_pdf_path,
            page_size="A4",
            margin="20mm"
        )

        # Actualizar la instancia con la ruta del PDF
        instance.status = "completed"
        instance.pdf_path = temp_pdf_path

        # Obtener el tamaño del archivo
        if os.path.exists(temp_pdf_path):
            instance.pdf_size = os.path.getsize(temp_pdf_path)

        await db.commit()

        # Retornar el archivo PDF
        filename = f"{safe_name.replace(' ', '_')}.pdf"

        logger.info("PDF generado para instancia: %s (ID: %s)", safe_name, instance_id)

        return FileResponse(
            path=temp_pdf_path,
            media_type='application/pdf',
            filename=filename,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        logger.exception("Error generando PDF para instancia %s", instance_id)
        instance.status = "error"
        instance.error_message = str(e)
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Error generando PDF: {str(e)}")
