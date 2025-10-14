"""
Get persona timeline endpoint - Vista PERSON-CENTERED
Timeline completo de TODOS los eventos y actividades de una persona.
"""

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, Path, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_async_session
from app.core.schemas.response import SuccessResponse
from app.core.security import RequireAnyRole
from app.domains.autenticacion.models import User
from app.domains.sujetos_epidemiologicos.ciudadanos_models import Ciudadano
from app.domains.sujetos_epidemiologicos.animales_models import Animal
from app.domains.eventos_epidemiologicos.eventos.models import (
    DetalleEventoSintomas,
    Evento,
)


class TimelineItem(BaseModel):
    """Item individual en el timeline de la persona"""

    tipo: str = Field(
        ...,
        description="Tipo de item: evento, sintoma, muestra, diagnostico, vacuna, internacion, tratamiento",
    )
    fecha: date = Field(..., description="Fecha del item")
    titulo: str = Field(..., description="Título descriptivo")
    descripcion: Optional[str] = Field(None, description="Descripción adicional")
    detalles: Optional[Dict[str, Any]] = Field(
        None, description="Detalles adicionales en formato JSON"
    )

    # Relación con evento padre
    evento_id: Optional[int] = Field(
        None, description="ID del evento al que pertenece (si aplica)"
    )
    evento_tipo: Optional[str] = Field(None, description="Tipo de ENO del evento")

    # Metadata
    clasificacion: Optional[str] = Field(None, description="Clasificación si es evento")
    es_critico: bool = Field(
        default=False, description="Si es un item crítico (muerte, UCI, confirmado)"
    )
    icono: str = Field(default="info", description="Icono sugerido para el frontend")
    color: str = Field(default="blue", description="Color sugerido para el frontend")

    model_config = ConfigDict(from_attributes=True)


class PersonaTimelineResponse(BaseModel):
    """Respuesta del timeline completo de una persona (PERSON-CENTERED)"""

    persona_id: int = Field(..., description="ID de la persona")
    tipo_sujeto: str = Field(..., description="Tipo: humano/animal")
    nombre_completo: str = Field(..., description="Nombre de la persona")

    # Timeline completo ordenado cronológicamente
    items: List[TimelineItem] = Field(
        default_factory=list, description="Items del timeline ordenados por fecha"
    )

    # Metadatos
    fecha_inicio: Optional[date] = Field(None, description="Fecha del primer item")
    fecha_fin: Optional[date] = Field(None, description="Fecha del último item")
    total_items: int = Field(..., description="Total de items en el timeline")
    total_eventos: int = Field(..., description="Total de eventos")

    model_config = ConfigDict(from_attributes=True)


logger = logging.getLogger(__name__)


async def get_persona_timeline(
    tipo_sujeto: str = Path(..., description="Tipo de sujeto: humano o animal"),
    persona_id: int = Path(..., description="ID de la persona"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(RequireAnyRole()),
) -> SuccessResponse[PersonaTimelineResponse]:
    """
    Obtiene el timeline completo de una persona.

    **Vista PERSON-CENTERED:**
    - Timeline unificado de TODOS los eventos de la persona
    - Incluye eventos, síntomas, muestras, diagnósticos, vacunas, internaciones
    - Ordenado cronológicamente
    - Ideal para visualización de historia clínica/epidemiológica

    **Casos de uso:**
    - Investigación de casos complejos
    - Seguimiento de casos recurrentes
    - Análisis de evolución temporal
    - Generación de reportes de caso
    """

    logger.info(
        f"📅 Obteniendo timeline de persona {tipo_sujeto}/{persona_id} para usuario {current_user.email}"
    )

    try:
        # Verificar que la persona existe
        nombre_completo = ""
        if tipo_sujeto == "humano":
            query = select(Ciudadano).where(Ciudadano.codigo_ciudadano == persona_id)
            result = await db.execute(query)
            persona = result.scalar_one_or_none()
            if not persona:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Ciudadano {persona_id} no encontrado",
                )
            nombre_completo = (
                f"{persona.nombre or ''} {persona.apellido or ''}".strip()
                or "Sin nombre"
            )

        elif tipo_sujeto == "animal":
            query = select(Animal).where(Animal.id == persona_id)
            result = await db.execute(query)
            persona = result.scalar_one_or_none()
            if not persona:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Animal {persona_id} no encontrado",
                )
            nombre_completo = persona.identificacion or f"{persona.especie} #{persona.id}"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="tipo_sujeto debe ser 'humano' o 'animal'",
            )

        # Obtener TODOS los eventos de la persona con TODAS sus relaciones
        if tipo_sujeto == "humano":
            eventos_query = (
                select(Evento)
                .where(Evento.codigo_ciudadano == persona_id)
                .options(
                    selectinload(Evento.tipo_eno),
                    selectinload(Evento.sintomas).selectinload(
                        DetalleEventoSintomas.sintoma
                    ),
                    selectinload(Evento.muestras),
                    selectinload(Evento.diagnosticos),
                    selectinload(Evento.vacunas),
                    selectinload(Evento.tratamientos),
                    selectinload(Evento.internaciones),
                    selectinload(Evento.investigaciones),
                    selectinload(Evento.contactos),
                    selectinload(Evento.antecedentes),
                    selectinload(Evento.ambitos_concurrencia),
                )
            )
        else:  # animal
            eventos_query = (
                select(Evento)
                .where(Evento.id_animal == persona_id)
                .options(
                    selectinload(Evento.tipo_eno),
                    selectinload(Evento.sintomas).selectinload(
                        DetalleEventoSintomas.sintoma
                    ),
                    selectinload(Evento.muestras),
                    selectinload(Evento.diagnosticos),
                    selectinload(Evento.vacunas),
                    selectinload(Evento.tratamientos),
                    selectinload(Evento.internaciones),
                    selectinload(Evento.investigaciones),
                    selectinload(Evento.contactos),
                    selectinload(Evento.antecedentes),
                    selectinload(Evento.ambitos_concurrencia),
                )
            )

        result = await db.execute(eventos_query)
        eventos = result.scalars().all()

        # Construir timeline con TODOS los items
        timeline_items = []

        for evento in eventos:
            evento_tipo_nombre = (
                evento.tipo_eno.nombre if evento.tipo_eno else f"Tipo {evento.id_tipo_eno}"
            )

            # 1. Item del evento principal
            es_critico_evento = evento.clasificacion_estrategia == "CONFIRMADOS"
            timeline_items.append(
                TimelineItem(
                    tipo="evento",
                    fecha=evento.fecha_minima_evento,
                    titulo=f"Evento {evento_tipo_nombre}",
                    descripcion=(
                        f"Caso #{evento.id_evento_caso} - "
                        f"{evento.clasificacion_estrategia or 'Sin clasificar'}"
                    ),
                    detalles={
                        "id_evento_caso": evento.id_evento_caso,
                        "clasificacion": evento.clasificacion_estrategia,
                        "confidence_score": evento.confidence_score,
                    },
                    evento_id=evento.id,
                    evento_tipo=evento_tipo_nombre,
                    clasificacion=evento.clasificacion_estrategia,
                    es_critico=es_critico_evento,
                    icono="activity" if not es_critico_evento else "alert-circle",
                    color="blue" if not es_critico_evento else "red",
                )
            )

            # 2. Síntomas del evento
            for sintoma_detalle in evento.sintomas or []:
                fecha_sintoma = (
                    sintoma_detalle.fecha_inicio_sintoma or evento.fecha_minima_evento
                )
                sintoma_nombre = (
                    sintoma_detalle.sintoma.signo_sintoma
                    if hasattr(sintoma_detalle, "sintoma")
                    and sintoma_detalle.sintoma
                    else "Síntoma no especificado"
                )
                timeline_items.append(
                    TimelineItem(
                        tipo="sintoma",
                        fecha=fecha_sintoma,
                        titulo=f"Síntoma: {sintoma_nombre}",
                        descripcion=f"Relacionado con evento {evento_tipo_nombre}",
                        evento_id=evento.id,
                        evento_tipo=evento_tipo_nombre,
                        icono="heart",
                        color="red",
                    )
                )

            # 3. Muestras del evento
            for muestra in evento.muestras or []:
                fecha_muestra = getattr(
                    muestra, "fecha_toma_muestra", None
                ) or evento.fecha_minima_evento
                tipo_muestra = getattr(muestra, "tipo_muestra", "Muestra")
                resultado = getattr(muestra, "resultado", None)

                timeline_items.append(
                    TimelineItem(
                        tipo="muestra",
                        fecha=fecha_muestra,
                        titulo=f"Muestra: {tipo_muestra}",
                        descripcion=(
                            f"Resultado: {resultado}" if resultado else "Pendiente"
                        ),
                        detalles={
                            "tipo": tipo_muestra,
                            "resultado": resultado,
                        },
                        evento_id=evento.id,
                        evento_tipo=evento_tipo_nombre,
                        icono="test-tube",
                        color="purple",
                        es_critico=resultado == "Positivo" if resultado else False,
                    )
                )

            # 4. Diagnósticos del evento
            for diagnostico in evento.diagnosticos or []:
                fecha_diagnostico = (
                    getattr(diagnostico, "fecha_diagnostico", None)
                    or evento.fecha_minima_evento
                )
                metodo = getattr(diagnostico, "metodo_diagnostico", "Diagnóstico")

                timeline_items.append(
                    TimelineItem(
                        tipo="diagnostico",
                        fecha=fecha_diagnostico,
                        titulo=f"Diagnóstico: {metodo}",
                        descripcion=f"Relacionado con evento {evento_tipo_nombre}",
                        evento_id=evento.id,
                        evento_tipo=evento_tipo_nombre,
                        icono="stethoscope",
                        color="green",
                    )
                )

            # 5. Vacunas del evento
            for vacuna in evento.vacunas or []:
                fecha_vacuna = (
                    getattr(vacuna, "fecha_ultima_dosis", None)
                    or evento.fecha_minima_evento
                )
                nombre_vacuna = getattr(vacuna, "nombre_vacuna", "Vacuna")

                timeline_items.append(
                    TimelineItem(
                        tipo="vacuna",
                        fecha=fecha_vacuna,
                        titulo=f"Vacuna: {nombre_vacuna}",
                        descripcion=f"Relacionado con evento {evento_tipo_nombre}",
                        detalles={
                            "nombre": nombre_vacuna,
                            "dosis": getattr(vacuna, "dosis_total", None),
                        },
                        evento_id=evento.id,
                        evento_tipo=evento_tipo_nombre,
                        icono="syringe",
                        color="indigo",
                    )
                )

            # 6. Tratamientos del evento
            for tratamiento in evento.tratamientos or []:
                fecha_tratamiento = (
                    getattr(tratamiento, "fecha_inicio_tratamiento", None)
                    or evento.fecha_minima_evento
                )
                descripcion_tratamiento = getattr(
                    tratamiento, "descripcion_tratamiento", "Tratamiento"
                )

                timeline_items.append(
                    TimelineItem(
                        tipo="tratamiento",
                        fecha=fecha_tratamiento,
                        titulo="Tratamiento",
                        descripcion=descripcion_tratamiento,
                        evento_id=evento.id,
                        evento_tipo=evento_tipo_nombre,
                        icono="pill",
                        color="orange",
                    )
                )

            # 7. Internaciones del evento
            for internacion in evento.internaciones or []:
                fecha_internacion = (
                    getattr(internacion, "fecha_internacion", None)
                    or evento.fecha_minima_evento
                )
                requirio_uci = getattr(internacion, "requirio_uci", False)
                es_fallecido = getattr(internacion, "es_fallecido", False)

                timeline_items.append(
                    TimelineItem(
                        tipo="internacion",
                        fecha=fecha_internacion,
                        titulo="Internación" + (" (UCI)" if requirio_uci else ""),
                        descripcion=(
                            "Resultado mortal"
                            if es_fallecido
                            else "Internación hospitalaria"
                        ),
                        detalles={
                            "requirio_uci": requirio_uci,
                            "es_fallecido": es_fallecido,
                        },
                        evento_id=evento.id,
                        evento_tipo=evento_tipo_nombre,
                        icono="building",
                        color="red" if requirio_uci or es_fallecido else "yellow",
                        es_critico=requirio_uci or es_fallecido,
                    )
                )

            # 8. Investigaciones del evento
            for investigacion in evento.investigaciones or []:
                fecha_investigacion = (
                    getattr(investigacion, "fecha_investigacion", None)
                    or evento.fecha_minima_evento
                )
                es_terreno = getattr(investigacion, "es_investigacion_terreno", False)

                timeline_items.append(
                    TimelineItem(
                        tipo="investigacion",
                        fecha=fecha_investigacion,
                        titulo=(
                            "Investigación de terreno" if es_terreno else "Investigación"
                        ),
                        descripcion=f"Investigación epidemiológica - Evento {evento_tipo_nombre}",
                        evento_id=evento.id,
                        evento_tipo=evento_tipo_nombre,
                        icono="search",
                        color="teal",
                    )
                )

        # Ordenar timeline por fecha (descendente - más reciente primero)
        timeline_items.sort(key=lambda x: x.fecha, reverse=True)

        # Calcular metadatos
        fechas = [item.fecha for item in timeline_items]
        fecha_inicio = min(fechas) if fechas else None
        fecha_fin = max(fechas) if fechas else None

        response = PersonaTimelineResponse(
            persona_id=persona_id,
            tipo_sujeto=tipo_sujeto,
            nombre_completo=nombre_completo,
            items=timeline_items,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            total_items=len(timeline_items),
            total_eventos=len(eventos),
        )

        logger.info(
            f"✅ Timeline de persona {tipo_sujeto}/{persona_id} obtenido: "
            f"{len(timeline_items)} items, {len(eventos)} eventos"
        )
        return SuccessResponse(data=response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"💥 Error obteniendo timeline de persona {tipo_sujeto}/{persona_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo timeline: {str(e)}",
        )
