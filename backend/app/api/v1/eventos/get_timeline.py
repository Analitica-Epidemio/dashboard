"""
Get evento timeline endpoint
"""

import logging
from datetime import date
from typing import Any

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import col

from app.core.database import get_async_session
from app.core.schemas.response import SuccessResponse
from app.core.security import RequireAnyRole
from app.domains.autenticacion.models import User
from app.domains.vigilancia_nominal.models.caso import CasoEpidemiologico
from app.domains.vigilancia_nominal.models.salud import MuestraCasoEpidemiologico


class CasoEpidemiologicoTimelineItem(BaseModel):
    """Item del timeline de un evento"""

    fecha: date = Field(..., description="Fecha del evento")
    tipo: str = Field(..., description="Tipo de evento")
    descripcion: str = Field(..., description="Descripción del evento")
    detalles: dict[str, Any] | None = Field(None, description="Detalles adicionales")


class CasoEpidemiologicoTimelineResponse(BaseModel):
    """Respuesta del timeline de un evento"""

    items: list[CasoEpidemiologicoTimelineItem] = Field(
        ..., description="Items del timeline"
    )
    total: int = Field(..., description="Total de items")


logger = logging.getLogger(__name__)


async def get_evento_timeline(
    evento_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(RequireAnyRole()),
) -> SuccessResponse[CasoEpidemiologicoTimelineResponse]:
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

    logger.info(
        f"📅 Generando timeline para evento {evento_id} - usuario: {current_user.email}"
    )

    try:
        # Obtener evento con todas las relaciones temporales
        query = (
            select(CasoEpidemiologico)
            .where(col(CasoEpidemiologico.id) == evento_id)
            .options(
                selectinload(CasoEpidemiologico.sintomas),
                selectinload(CasoEpidemiologico.muestras).selectinload(
                    MuestraCasoEpidemiologico.muestra
                ),
                selectinload(CasoEpidemiologico.diagnosticos),
                selectinload(CasoEpidemiologico.internaciones),
                selectinload(CasoEpidemiologico.vacunas),
            )
        )

        result = await db.execute(query)
        evento = result.scalar_one_or_none()

        if not evento:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"CasoEpidemiologico {evento_id} no encontrado",
            )

        timeline_items = []

        # Agregar eventos principales
        if evento.fecha_inicio_sintomas:
            timeline_items.append(
                CasoEpidemiologicoTimelineItem(
                    fecha=evento.fecha_inicio_sintomas,
                    tipo="inicio_sintomas",
                    descripcion="Inicio de síntomas",
                    detalles={"sintomatico": evento.es_caso_sintomatico},
                )
            )

        if evento.fecha_primera_consulta:
            timeline_items.append(
                CasoEpidemiologicoTimelineItem(
                    fecha=evento.fecha_primera_consulta,
                    tipo="consulta",
                    descripcion="Primera consulta médica",
                    detalles=None,
                )
            )

        if evento.fecha_apertura_caso:
            timeline_items.append(
                CasoEpidemiologicoTimelineItem(
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
        timeline_items.extend(
            CasoEpidemiologicoTimelineItem(
                fecha=sintoma.fecha_inicio_sintoma,
                tipo="sintoma",
                descripcion=f"Síntoma: {sintoma.sintoma.signo_sintoma}",
                detalles=None,
            )
            for sintoma in evento.sintomas or []
            if (
                sintoma.fecha_inicio_sintoma
                and sintoma.sintoma
                and sintoma.sintoma.signo_sintoma
            )
        )

        # Agregar muestras
        timeline_items.extend(
            CasoEpidemiologicoTimelineItem(
                fecha=muestra.fecha_toma_muestra,
                tipo="muestra",
                descripcion=f"Muestra: {muestra.muestra.descripcion}",
                detalles={"resultado": muestra.valor},
            )
            for muestra in evento.muestras or []
            if (
                muestra.fecha_toma_muestra
                and muestra.muestra
                and muestra.muestra.descripcion
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
                        CasoEpidemiologicoTimelineItem(
                            fecha=diagnostico.fecha_diagnostico_referido,
                            tipo="diagnostico",
                            descripcion=f"Diagnóstico: {diagnostico_text}",
                            detalles={
                                "clasificacion": diagnostico.clasificacion_manual
                            },
                        )
                    )

        # Ordenar cronológicamente
        timeline_items.sort(key=lambda x: x.fecha)

        response = CasoEpidemiologicoTimelineResponse(
            items=timeline_items, total=len(timeline_items)
        )

        logger.info(f"✅ Timeline generado con {len(timeline_items)} eventos")
        return SuccessResponse(data=response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Error generando timeline: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generando timeline: {e!s}",
        ) from e
