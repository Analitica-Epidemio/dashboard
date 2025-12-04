"""
Get evento timeline endpoint
"""

import logging
from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_async_session
from app.core.schemas.response import SuccessResponse
from app.core.security import RequireAnyRole
from app.domains.atencion_medica.salud_models import MuestraEvento
from app.domains.autenticacion.models import User
from app.domains.eventos_epidemiologicos.eventos.models import Evento


class EventoTimelineItem(BaseModel):
    """Item del timeline de un evento"""

    fecha: date = Field(..., description="Fecha del evento")
    tipo: str = Field(..., description="Tipo de evento")
    descripcion: str = Field(..., description="Descripción del evento")
    detalles: Optional[Dict[str, Any]] = Field(None, description="Detalles adicionales")


class EventoTimelineResponse(BaseModel):
    """Respuesta del timeline de un evento"""

    items: List[EventoTimelineItem] = Field(..., description="Items del timeline")
    total: int = Field(..., description="Total de items")

logger = logging.getLogger(__name__)


async def get_evento_timeline(
    evento_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(RequireAnyRole())
) -> SuccessResponse[EventoTimelineResponse]:
    """
    Obtiene el timeline cronológico de un evento.

    **Incluye eventos de:**
    - Inicio de síntomas
    - Consultas médicas
    - Toma de muestras
    - Resultados de laboratorio
    - Diagnósticos
    - Internaciones
    - Vacunaciones

    Ordenado cronológicamente.
    """

    logger.info(f"📅 Generando timeline para evento {evento_id} - usuario: {current_user.email}")

    try:
        # Obtener evento con todas las relaciones temporales
        query = (
            select(Evento)
            .where(Evento.id == evento_id)
            .options(
                selectinload(Evento.sintomas),
                selectinload(Evento.muestras).selectinload(MuestraEvento.muestra),
                selectinload(Evento.diagnosticos),
                selectinload(Evento.internaciones),
                selectinload(Evento.vacunas),
            )
        )

        result = await db.execute(query)
        evento = result.scalar_one_or_none()

        if not evento:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Evento {evento_id} no encontrado",
            )

        timeline_items = []

        # Agregar eventos principales
        if evento.fecha_inicio_sintomas:
            timeline_items.append(
                EventoTimelineItem(
                    fecha=evento.fecha_inicio_sintomas,
                    tipo="inicio_sintomas",
                    descripcion="Inicio de síntomas",
                    detalles={"sintomatico": evento.es_caso_sintomatico},
                )
            )

        if evento.fecha_primera_consulta:
            timeline_items.append(
                EventoTimelineItem(
                    fecha=evento.fecha_primera_consulta,
                    tipo="consulta",
                    descripcion="Primera consulta médica",
                    detalles=None,
                )
            )

        if evento.fecha_apertura_caso:
            timeline_items.append(
                EventoTimelineItem(
                    fecha=evento.fecha_apertura_caso,
                    tipo="apertura_caso",
                    descripcion="Apertura del caso en el sistema",
                    detalles={
                        "semana_epidemiologica": evento.semana_epidemiologica_apertura,
                        "anio": evento.anio_epidemiologico_apertura,
                    },
                )
            )

        # Agregar síntomas detallados
        for sintoma in evento.sintomas or []:
            if sintoma.fecha_inicio_sintoma and sintoma.sintoma and sintoma.sintoma.signo_sintoma:
                timeline_items.append(
                    EventoTimelineItem(
                        fecha=sintoma.fecha_inicio_sintoma,
                        tipo="sintoma",
                        descripcion=f"Síntoma: {sintoma.sintoma.signo_sintoma}",
                        detalles=None,
                    )
                )

        # Agregar muestras
        for muestra in evento.muestras or []:
            if muestra.fecha_toma_muestra and muestra.muestra and muestra.muestra.descripcion:
                timeline_items.append(
                    EventoTimelineItem(
                        fecha=muestra.fecha_toma_muestra,
                        tipo="muestra",
                        descripcion=f"Muestra: {muestra.muestra.descripcion}",
                        detalles={"resultado": muestra.valor},
                    )
                )

        # Agregar diagnósticos
        for diagnostico in evento.diagnosticos or []:
            if diagnostico.fecha_diagnostico_referido:
                diagnostico_text = (
                    diagnostico.clasificacion_manual
                    or diagnostico.clasificacion_automatica
                    or diagnostico.diagnostico_referido
                )
                if diagnostico_text:
                    timeline_items.append(
                        EventoTimelineItem(
                            fecha=diagnostico.fecha_diagnostico_referido,
                            tipo="diagnostico",
                            descripcion=f"Diagnóstico: {diagnostico_text}",
                            detalles={"clasificacion": diagnostico.clasificacion_manual},
                        )
                    )

        # Ordenar cronológicamente
        timeline_items.sort(key=lambda x: x.fecha)

        response = EventoTimelineResponse(
            items=timeline_items, total=len(timeline_items)
        )

        logger.info(f"✅ Timeline generado con {len(timeline_items)} eventos")
        return SuccessResponse(data=response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Error generando timeline: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generando timeline: {str(e)}",
        )
