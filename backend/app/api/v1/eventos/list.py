"""
Endpoint para listado de eventos epidemiológicos.
"""

import logging
from datetime import date
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import String, and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_async_session
from app.core.schemas.response import SuccessResponse
from app.core.security import RequireAnyRole
from app.domains.autenticacion.models import User
from app.domains.sujetos_epidemiologicos.ciudadanos_models.models import (
    Animal,
    Ciudadano,
    CiudadanoDomicilio,
)
from app.domains.estrategias.models import TipoClasificacion
from app.domains.eventos.models import Evento, TipoEno
from app.domains.localidades.models import Departamento, Localidad


class EventoSortBy(str, Enum):
    FECHA_DESC = "fecha_desc"
    FECHA_ASC = "fecha_asc"
    ID_DESC = "id_desc"
    ID_ASC = "id_asc"
    TIPO_ENO = "tipo_eno"


class EventoListItem(BaseModel):
    """Item individual en la lista de eventos"""

    id: int = Field(..., description="ID del evento")
    id_evento_caso: int = Field(..., description="ID único del caso")
    tipo_eno_id: int = Field(..., description="ID del tipo ENO")
    tipo_eno_nombre: Optional[str] = Field(None, description="Nombre del tipo ENO")
    fecha_minima_evento: date = Field(..., description="Fecha del evento")
    fecha_inicio_sintomas: Optional[date] = Field(
        None, description="Fecha de inicio de síntomas"
    )
    clasificacion_estrategia: Optional[TipoClasificacion] = Field(None, description="Clasificación estratégica del evento")
    es_positivo: Optional[bool] = Field(None, description="Si es positivo")
    confidence_score: Optional[float] = Field(None, description="Score de confianza")

    # Datos del sujeto
    tipo_sujeto: str = Field(
        ..., description="Tipo de sujeto: humano/animal/desconocido"
    )
    nombre_sujeto: Optional[str] = Field(None, description="Nombre del sujeto")
    documento_sujeto: Optional[str] = Field(None, description="Documento del sujeto")
    edad: Optional[int] = Field(None, description="Edad en años")
    sexo: Optional[str] = Field(None, description="Sexo del sujeto")

    # Ubicación
    provincia: Optional[str] = Field(None, description="Provincia de residencia")
    localidad: Optional[str] = Field(None, description="Localidad de residencia")

    # Estados
    es_caso_sintomatico: Optional[bool] = Field(
        None, description="Si presenta síntomas"
    )
    requiere_revision_especie: Optional[bool] = Field(
        None, description="Si requiere revisión"
    )
    con_resultado_mortal: Optional[bool] = Field(
        None, description="Si tuvo resultado mortal"
    )

    # Conteos
    cantidad_sintomas: int = Field(0, description="Cantidad de síntomas registrados")
    cantidad_muestras: int = Field(0, description="Cantidad de muestras tomadas")
    cantidad_diagnosticos: int = Field(0, description="Cantidad de diagnósticos")

    model_config = ConfigDict(from_attributes=True)


class PaginationInfo(BaseModel):
    """Información de paginación"""

    page: int = Field(..., description="Página actual")
    page_size: int = Field(..., description="Tamaño de página")
    total: int = Field(..., description="Total de registros")
    total_pages: int = Field(..., description="Total de páginas")
    has_next: bool = Field(..., description="Si hay página siguiente")
    has_prev: bool = Field(..., description="Si hay página anterior")


class EventoListResponse(BaseModel):
    """Respuesta completa del listado de eventos"""

    data: List[EventoListItem] = Field(..., description="Lista de eventos")
    pagination: PaginationInfo = Field(..., description="Información de paginación")
    filters_applied: Dict[str, Any] = Field(..., description="Filtros aplicados")

logger = logging.getLogger(__name__)


async def list_eventos(
    # Paginación
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(50, ge=10, le=200, description="Tamaño de página"),
    # Búsqueda
    search: Optional[str] = Query(
        None, description="Búsqueda por ID, nombre o documento"
    ),
    # Filtros
    tipo_eno_id: Optional[int] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    clasificacion: Optional[str] = None,
    es_positivo: Optional[bool] = None,
    provincia: Optional[str] = None,
    tipo_sujeto: Optional[str] = None,
    requiere_revision: Optional[bool] = None,
    # Ordenamiento
    sort_by: EventoSortBy = EventoSortBy.FECHA_DESC,
    # DB and Auth
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(RequireAnyRole()),
) -> SuccessResponse[EventoListResponse]:
    """
    Lista eventos epidemiológicos con filtros y paginación.

    **Características:**
    - Búsqueda por ID evento, nombre ciudadano o documento
    - Filtros múltiples combinables
    - Paginación eficiente
    - Incluye conteos de relaciones

    **Performance:**
    - Usa índices optimizados
    - Carga solo datos necesarios para listado
    - Límite máximo 200 registros por página
    """

    logger.info(f"📋 Listando eventos - page: {page}, user: {current_user.email}")

    try:
        # Query base con joins necesarios (EVENT-CENTERED)
        query = (
            select(Evento)
            .outerjoin(TipoEno, Evento.id_tipo_eno == TipoEno.id)
            .outerjoin(Ciudadano, Evento.codigo_ciudadano == Ciudadano.codigo_ciudadano)
            .outerjoin(Animal, Evento.id_animal == Animal.id)
            .options(
                selectinload(Evento.tipo_eno),
                # Relaciones con sujetos (ciudadano/animal)
                selectinload(Evento.ciudadano)
                .selectinload(Ciudadano.domicilios)
                .selectinload(CiudadanoDomicilio.localidad)
                .selectinload(Localidad.departamento)
                .selectinload(Departamento.provincia),
                selectinload(Evento.ciudadano).selectinload(Ciudadano.datos),
                selectinload(Evento.animal)
                .selectinload(Animal.localidad)
                .selectinload(Localidad.departamento)
                .selectinload(Departamento.provincia),
                # Relaciones con establecimientos
                selectinload(Evento.establecimiento_consulta),
                selectinload(Evento.establecimiento_notificacion),
                selectinload(Evento.establecimiento_carga),
                # Relaciones de salud y diagnósticos
                selectinload(Evento.sintomas),
                selectinload(Evento.muestras),
                selectinload(Evento.diagnosticos),
                selectinload(Evento.internaciones),
                selectinload(Evento.tratamientos),
                # Relaciones epidemiológicas
                selectinload(Evento.antecedentes),
                selectinload(Evento.investigaciones),
                selectinload(Evento.contactos),
                selectinload(Evento.ambitos_concurrencia),
                # Relaciones de prevención
                selectinload(Evento.vacunas),
            )
        )

        # Aplicar búsqueda
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Evento.id_evento_caso.cast(String).ilike(search_term),
                    Ciudadano.nombre.ilike(search_term),
                    Ciudadano.apellido.ilike(search_term),
                    Ciudadano.numero_documento.cast(String).ilike(search_term),
                    Animal.especie.ilike(search_term),
                )
            )

        # Aplicar filtros
        conditions = []

        if tipo_eno_id:
            conditions.append(Evento.id_tipo_eno == tipo_eno_id)

        if fecha_desde:
            conditions.append(Evento.fecha_minima_evento >= fecha_desde)

        if fecha_hasta:
            conditions.append(Evento.fecha_minima_evento <= fecha_hasta)

        if clasificacion:
            conditions.append(Evento.clasificacion_estrategia == clasificacion)

        if es_positivo is not None:
            conditions.append(Evento.es_positivo == es_positivo)

        if provincia:
            conditions.append(Ciudadano.provincia_residencia == provincia)

        if tipo_sujeto:
            if tipo_sujeto == "humano":
                conditions.append(Evento.codigo_ciudadano.isnot(None))
            elif tipo_sujeto == "animal":
                conditions.append(Evento.id_animal.isnot(None))

        if requiere_revision is not None:
            conditions.append(Evento.requiere_revision_especie == requiere_revision)

        if conditions:
            query = query.where(and_(*conditions))

        # Aplicar ordenamiento
        if sort_by == EventoSortBy.FECHA_DESC:
            query = query.order_by(desc(Evento.fecha_minima_evento))
        elif sort_by == EventoSortBy.FECHA_ASC:
            query = query.order_by(Evento.fecha_minima_evento)
        elif sort_by == EventoSortBy.ID_DESC:
            query = query.order_by(desc(Evento.id_evento_caso))
        elif sort_by == EventoSortBy.ID_ASC:
            query = query.order_by(Evento.id_evento_caso)
        elif sort_by == EventoSortBy.TIPO_ENO:
            query = query.order_by(TipoEno.nombre, desc(Evento.fecha_minima_evento))

        # Contar total antes de paginar
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Aplicar paginación
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Ejecutar query
        result = await db.execute(query)
        eventos = result.scalars().all()

        # Preparar respuesta
        eventos_list = []
        for evento in eventos:
            # Determinar tipo de sujeto y datos
            tipo_sujeto = "desconocido"
            nombre_sujeto = None
            documento_sujeto = None
            edad = None
            sexo = None
            provincia_res = None
            localidad_res = None

            if evento.ciudadano:
                tipo_sujeto = "humano"
                nombre_sujeto = (
                    f"{evento.ciudadano.nombre} {evento.ciudadano.apellido}".strip()
                )
                documento_sujeto = (
                    str(evento.ciudadano.numero_documento)
                    if evento.ciudadano.numero_documento
                    else None
                )
                edad = evento.edad_anos_al_momento_apertura
                sexo = evento.ciudadano.sexo_biologico

                # Get location from first domicilio
                if evento.ciudadano.domicilios:
                    primer_domicilio = evento.ciudadano.domicilios[0]
                    if primer_domicilio.localidad:
                        localidad_res = primer_domicilio.localidad.nombre
                        if (
                            primer_domicilio.localidad.departamento
                            and primer_domicilio.localidad.departamento.provincia
                        ):
                            provincia_res = (
                                primer_domicilio.localidad.departamento.provincia.nombre
                            )
                        else:
                            provincia_res = None
                    else:
                        localidad_res = None
                        provincia_res = None
                else:
                    localidad_res = None
                    provincia_res = None
            elif evento.animal:
                tipo_sujeto = "animal"
                nombre_sujeto = evento.animal.identificacion or f"{evento.animal.especie} #{evento.animal.id}"

                # Get location from animal's localidad
                if evento.animal.localidad:
                    localidad_res = evento.animal.localidad.nombre
                    if (
                        evento.animal.localidad.departamento
                        and evento.animal.localidad.departamento.provincia
                    ):
                        provincia_res = (
                            evento.animal.localidad.departamento.provincia.nombre
                        )
                    else:
                        provincia_res = None
                else:
                    localidad_res = None
                    provincia_res = None

            eventos_list.append(
                EventoListItem(
                    id=evento.id,
                    id_evento_caso=evento.id_evento_caso,
                    tipo_eno_id=evento.id_tipo_eno,
                    tipo_eno_nombre=evento.tipo_eno.nombre if evento.tipo_eno else None,
                    fecha_minima_evento=evento.fecha_minima_evento,
                    fecha_inicio_sintomas=evento.fecha_inicio_sintomas,
                    clasificacion_estrategia=evento.clasificacion_estrategia,
                    es_positivo=evento.es_positivo,
                    confidence_score=evento.confidence_score,
                    tipo_sujeto=tipo_sujeto,
                    nombre_sujeto=nombre_sujeto,
                    documento_sujeto=documento_sujeto,
                    edad=edad,
                    sexo=sexo,
                    provincia=provincia_res,
                    localidad=localidad_res,
                    es_caso_sintomatico=evento.es_caso_sintomatico,
                    requiere_revision_especie=evento.requiere_revision_especie,
                    con_resultado_mortal=bool(
                        any(
                            d.es_fallecido
                            for d in (evento.internaciones or [])
                        )
                    ),
                    cantidad_sintomas=len(evento.sintomas or []),
                    cantidad_muestras=len(evento.muestras or []),
                    cantidad_diagnosticos=len(evento.diagnosticos or []),
                )
            )

        # Respuesta con metadata de paginación
        response = EventoListResponse(
            data=eventos_list,
            pagination=PaginationInfo(
                page=page,
                page_size=page_size,
                total=total,
                total_pages=(total + page_size - 1) // page_size,
                has_next=offset + page_size < total,
                has_prev=page > 1,
            ),
            filters_applied={
                "search": search,
                "tipo_eno_id": tipo_eno_id,
                "fecha_desde": fecha_desde,
                "fecha_hasta": fecha_hasta,
                "clasificacion": clasificacion,
                "tipo_sujeto": tipo_sujeto,
            },
        )

        logger.info(f"✅ Encontrados {len(eventos_list)} eventos de {total} total")
        return SuccessResponse(data=response)

    except Exception as e:
        logger.error(f"💥 Error listando eventos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo eventos: {str(e)}",
        )