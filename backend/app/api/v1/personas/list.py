"""
Endpoint para listado de personas (ciudadanos/animales) con sus eventos agrupados.
Vista PERSON-CENTERED: cada item es una persona con resumen de TODOS sus eventos.

OPTIMIZADO: Usa agregaciones SQL nativas para evitar N+1 queries.
"""

import logging
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any

from fastapi import Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import String, case, cast, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from app.core.database import get_async_session
from app.core.schemas.response import SuccessResponse
from app.core.security import RequireAnyRole
from app.domains.autenticacion.models import User
from app.domains.territorio.establecimientos_models import Establecimiento
from app.domains.territorio.geografia_models import Departamento, Localidad, Provincia
from app.domains.vigilancia_nominal.clasificacion.models import TipoClasificacion
from app.domains.vigilancia_nominal.models.caso import CasoEpidemiologico
from app.domains.vigilancia_nominal.models.enfermedad import (
    Enfermedad,
    EnfermedadGrupo,
)
from app.domains.vigilancia_nominal.models.sujetos import Ciudadano


class PersonaSortBy(str, Enum):
    NOMBRE_ASC = "nombre_asc"
    NOMBRE_DESC = "nombre_desc"
    EVENTOS_DESC = "eventos_desc"
    EVENTOS_ASC = "eventos_asc"
    ULTIMO_EVENTO_DESC = "ultimo_evento_desc"
    ULTIMO_EVENTO_ASC = "ultimo_evento_asc"


class PersonaListItem(BaseModel):
    """Item individual en la lista de personas (PERSON-CENTERED)"""

    # Identificación de la persona
    tipo_sujeto: str = Field(..., description="Tipo: humano/animal")
    persona_id: int = Field(
        ..., description="ID de la persona (codigo_ciudadano o id_animal)"
    )

    # Datos básicos
    nombre_completo: str = Field(..., description="Nombre completo o identificación")
    documento: str | None = Field(None, description="Documento (solo humanos)")
    edad_actual: int | None = Field(None, description="Edad actual en años")
    sexo: str | None = Field(None, description="Sexo/género")

    # Ubicación
    provincia: str | None = Field(None, description="Provincia de residencia")
    localidad: str | None = Field(None, description="Localidad de residencia")

    # Estadísticas de eventos de esta persona
    total_eventos: int = Field(..., description="Total de eventos registrados")
    eventos_confirmados: int = Field(0, description="CasoEpidemiologicos confirmados")
    eventos_sospechosos: int = Field(0, description="CasoEpidemiologicos sospechosos")
    eventos_probables: int = Field(0, description="CasoEpidemiologicos probables")
    eventos_descartados: int = Field(0, description="CasoEpidemiologicos descartados")

    # Fechas relevantes
    primer_evento_fecha: date | None = Field(
        None, description="Fecha del primer evento"
    )
    ultimo_evento_fecha: date | None = Field(
        None, description="Fecha del último evento"
    )

    # Información del último evento
    ultimo_evento_tipo: str | None = Field(None, description="Tipo del último ENO")
    ultimo_evento_clasificacion: str | None = Field(
        None, description="Clasificación del último evento"
    )

    # Flags importantes
    tiene_eventos_activos: bool = Field(
        default=False, description="Si tiene eventos activos (últimos 30 días)"
    )

    model_config = ConfigDict(from_attributes=True)


class PaginationInfo(BaseModel):
    """Información de paginación"""

    page: int = Field(..., description="Página actual")
    page_size: int = Field(..., description="Tamaño de página")
    total: int = Field(..., description="Total de registros")
    total_pages: int = Field(..., description="Total de páginas")
    has_next: bool = Field(..., description="Si hay página siguiente")
    has_prev: bool = Field(..., description="Si hay página anterior")


class AggregatedStats(BaseModel):
    """Estadísticas agregadas sobre TODAS las personas que coinciden con los filtros"""

    total_personas: int = Field(
        ..., description="Total de personas (mismo que pagination.total)"
    )
    personas_con_multiples_eventos: int = Field(
        0, description="Personas con más de un evento"
    )
    personas_con_confirmados: int = Field(
        0, description="Personas con al menos un evento confirmado"
    )
    personas_activas: int = Field(
        0, description="Personas con eventos en últimos 30 días"
    )


class PersonaListResponse(BaseModel):
    """Respuesta completa del listado de personas (PERSON-CENTERED)"""

    data: list[PersonaListItem] = Field(..., description="Lista de personas")
    pagination: PaginationInfo = Field(..., description="Información de paginación")
    stats: AggregatedStats = Field(
        ..., description="Estadísticas agregadas sobre todos los resultados"
    )
    filters_applied: dict[str, Any] = Field(..., description="Filtros aplicados")


logger = logging.getLogger(__name__)


async def list_personas(
    # Paginación
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(50, ge=10, le=200, description="Tamaño de página"),
    # Búsqueda
    search: str | None = Query(
        None, description="Búsqueda por nombre, apellido o documento"
    ),
    # Filtros
    tipo_sujeto: str | None = Query(
        None, description="Filtro por tipo: humano, animal, todos"
    ),
    provincia_ids_establecimiento: list[int] | None = Query(
        None,
        description="Lista de códigos INDEC de provincias (filtro por ESTABLECIMIENTO DE NOTIFICACIÓN de eventos)",
        alias="provincia_id",  # Mantiene compatibilidad con frontend
    ),
    tipo_eno_ids: list[int] | None = Query(
        None, description="Lista de IDs de tipos de eventos"
    ),
    grupo_eno_ids: list[int] | None = Query(
        None, description="Lista de IDs de grupos de eventos"
    ),
    tiene_multiples_eventos: bool | None = Query(
        None, description="Solo personas con múltiples eventos"
    ),
    edad_min: int | None = Query(None, ge=0, le=120, description="Edad mínima"),
    edad_max: int | None = Query(None, ge=0, le=120, description="Edad máxima"),
    # Ordenamiento
    sort_by: PersonaSortBy = PersonaSortBy.ULTIMO_EVENTO_DESC,
    # DB and Auth
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(RequireAnyRole()),
) -> SuccessResponse[PersonaListResponse]:
    """
    Lista personas (ciudadanos/animales) con sus eventos agrupados.

    **Vista PERSON-CENTERED optimizada:**
    - Usa agregaciones SQL para máxima performance
    - Evita N+1 queries
    - Procesa TODO en base de datos
    """

    logger.info(f"📋 Listando personas - page: {page}, user: {current_user.email}")

    try:
        # Determinar si buscar ciudadanos, animales o ambos
        buscar_ciudadanos = tipo_sujeto in [None, "humano", "todos"]
        buscar_animales = tipo_sujeto in [None, "animal", "todos"]

        hace_30_dias = datetime.now().date() - timedelta(days=30)

        # === QUERY OPTIMIZADA PARA CIUDADANOS CON AGREGACIONES SQL ===
        if buscar_ciudadanos:
            # Subquery con TODAS las agregaciones en SQL (una sola query)
            # IMPORTANTE: Incluye JOINs para filtrar por provincia de ESTABLECIMIENTO DE NOTIFICACIÓN
            eventos_base_query = (
                select(CasoEpidemiologico)
                .outerjoin(
                    Enfermedad,
                    col(CasoEpidemiologico.id_enfermedad) == col(Enfermedad.id),
                )
                .outerjoin(
                    EnfermedadGrupo,
                    col(Enfermedad.id) == col(EnfermedadGrupo.id_enfermedad),
                )
                # JOINs para filtro de provincia por ESTABLECIMIENTO DE NOTIFICACIÓN
                .outerjoin(
                    Establecimiento,
                    col(CasoEpidemiologico.id_establecimiento_notificacion)
                    == col(Establecimiento.id),
                )
                .outerjoin(
                    Localidad,
                    col(Establecimiento.id_localidad_indec)
                    == col(Localidad.id_localidad_indec),
                )
                .outerjoin(
                    Departamento,
                    col(Localidad.id_departamento_indec)
                    == col(Departamento.id_departamento_indec),
                )
                .outerjoin(
                    Provincia,
                    col(Departamento.id_provincia_indec)
                    == col(Provincia.id_provincia_indec),
                )
                .where(col(CasoEpidemiologico.codigo_ciudadano).isnot(None))
            )

            # Aplicar filtros de eventos
            if provincia_ids_establecimiento:
                eventos_base_query = eventos_base_query.where(
                    col(Provincia.id_provincia_indec).in_(provincia_ids_establecimiento)
                )

            if tipo_eno_ids:
                eventos_base_query = eventos_base_query.where(
                    col(CasoEpidemiologico.id_enfermedad).in_(tipo_eno_ids)
                )

            if grupo_eno_ids:
                eventos_base_query = eventos_base_query.where(
                    col(EnfermedadGrupo.id_grupo).in_(grupo_eno_ids)
                )

            # Filtros de edad (calcular edad a partir de fecha_nacimiento y fecha_apertura_caso)
            if edad_min is not None or edad_max is not None:
                # Calcular edad usando AGE(fecha_apertura_caso, fecha_nacimiento)
                edad_calculada = func.extract(
                    "year",
                    func.age(
                        CasoEpidemiologico.fecha_apertura_caso,
                        CasoEpidemiologico.fecha_nacimiento,
                    ),
                )
                # Asegurarse de que ambas fechas existan
                eventos_base_query = eventos_base_query.where(
                    col(CasoEpidemiologico.fecha_nacimiento).isnot(None),
                    col(CasoEpidemiologico.fecha_apertura_caso).isnot(None),
                )

                if edad_min is not None:
                    eventos_base_query = eventos_base_query.where(
                        edad_calculada >= edad_min
                    )

                if edad_max is not None:
                    eventos_base_query = eventos_base_query.where(
                        edad_calculada <= edad_max
                    )

            # Crear subquery filtrada
            eventos_filtrados = eventos_base_query.subquery()

            # Ahora agregar con los eventos filtrados
            eventos_stats_subq = (
                select(
                    eventos_filtrados.c.codigo_ciudadano,
                    func.count(func.distinct(eventos_filtrados.c.id)).label(
                        "total_eventos"
                    ),
                    func.sum(
                        case(
                            (
                                eventos_filtrados.c.clasificacion_estrategia
                                == TipoClasificacion.CONFIRMADOS,
                                1,
                            ),
                            else_=0,
                        )
                    ).label("confirmados"),
                    func.sum(
                        case(
                            (
                                eventos_filtrados.c.clasificacion_estrategia
                                == TipoClasificacion.SOSPECHOSOS,
                                1,
                            ),
                            else_=0,
                        )
                    ).label("sospechosos"),
                    func.sum(
                        case(
                            (
                                eventos_filtrados.c.clasificacion_estrategia
                                == TipoClasificacion.PROBABLES,
                                1,
                            ),
                            else_=0,
                        )
                    ).label("probables"),
                    func.sum(
                        case(
                            (
                                eventos_filtrados.c.clasificacion_estrategia
                                == TipoClasificacion.DESCARTADOS,
                                1,
                            ),
                            else_=0,
                        )
                    ).label("descartados"),
                    func.min(eventos_filtrados.c.fecha_minima_caso).label(
                        "primer_evento"
                    ),
                    func.max(eventos_filtrados.c.fecha_minima_caso).label(
                        "ultimo_evento"
                    ),
                    func.sum(
                        case(
                            (eventos_filtrados.c.fecha_minima_caso >= hace_30_dias, 1),
                            else_=0,
                        )
                    ).label("eventos_recientes"),
                )
                .where(col(eventos_filtrados.c.codigo_ciudadano).isnot(None))
                .group_by(eventos_filtrados.c.codigo_ciudadano)
                .subquery()
            )

            # Subquery para obtener el último evento con su tipo (usa eventos filtrados)
            ultimo_evento_subq = (
                select(
                    eventos_filtrados.c.codigo_ciudadano,
                    eventos_filtrados.c.id_enfermedad,
                    eventos_filtrados.c.clasificacion_estrategia,
                    func.row_number()
                    .over(
                        partition_by=eventos_filtrados.c.codigo_ciudadano,
                        order_by=desc(eventos_filtrados.c.fecha_minima_caso),
                    )
                    .label("rn"),
                )
                .where(col(eventos_filtrados.c.codigo_ciudadano).isnot(None))
                .subquery()
            )

            ultimo_evento_filtrado = (
                select(
                    ultimo_evento_subq.c.codigo_ciudadano,
                    ultimo_evento_subq.c.id_enfermedad,
                    ultimo_evento_subq.c.clasificacion_estrategia,
                )
                .where(ultimo_evento_subq.c.rn == 1)
                .subquery()
            )

            # Query principal con JOINS
            ciudadanos_query = (
                select(
                    Ciudadano,
                    eventos_stats_subq.c.total_eventos,
                    eventos_stats_subq.c.confirmados,
                    eventos_stats_subq.c.sospechosos,
                    eventos_stats_subq.c.probables,
                    eventos_stats_subq.c.descartados,
                    eventos_stats_subq.c.primer_evento,
                    eventos_stats_subq.c.ultimo_evento,
                    eventos_stats_subq.c.eventos_recientes,
                    ultimo_evento_filtrado.c.clasificacion_estrategia.label(
                        "ultimo_evento_clasificacion"
                    ),
                    col(Enfermedad.nombre).label("ultimo_evento_tipo"),
                )
                .outerjoin(
                    eventos_stats_subq,
                    col(Ciudadano.codigo_ciudadano)
                    == eventos_stats_subq.c.codigo_ciudadano,
                )
                .outerjoin(
                    ultimo_evento_filtrado,
                    col(Ciudadano.codigo_ciudadano)
                    == ultimo_evento_filtrado.c.codigo_ciudadano,
                )
                .outerjoin(
                    Enfermedad,
                    ultimo_evento_filtrado.c.id_enfermedad == col(Enfermedad.id),
                )
                .where(col(eventos_stats_subq.c.total_eventos).isnot(None))
            )

            # Aplicar filtros de búsqueda
            if search:
                search_term = f"%{search}%"
                ciudadanos_query = ciudadanos_query.where(
                    or_(
                        col(Ciudadano.nombre).ilike(search_term),
                        col(Ciudadano.apellido).ilike(search_term),
                        cast(col(Ciudadano.numero_documento), String).ilike(
                            search_term
                        ),
                    )
                )

            # Aplicar filtros adicionales
            if tiene_multiples_eventos:
                ciudadanos_query = ciudadanos_query.where(
                    eventos_stats_subq.c.total_eventos > 1
                )

            # Aplicar ordenamiento
            if sort_by == PersonaSortBy.NOMBRE_ASC:
                ciudadanos_query = ciudadanos_query.order_by(col(Ciudadano.nombre))
            elif sort_by == PersonaSortBy.NOMBRE_DESC:
                ciudadanos_query = ciudadanos_query.order_by(
                    desc(col(Ciudadano.nombre))
                )
            elif sort_by == PersonaSortBy.EVENTOS_DESC:
                ciudadanos_query = ciudadanos_query.order_by(
                    desc(eventos_stats_subq.c.total_eventos)
                )
            elif sort_by == PersonaSortBy.EVENTOS_ASC:
                ciudadanos_query = ciudadanos_query.order_by(
                    eventos_stats_subq.c.total_eventos
                )
            elif sort_by == PersonaSortBy.ULTIMO_EVENTO_DESC:
                ciudadanos_query = ciudadanos_query.order_by(
                    desc(eventos_stats_subq.c.ultimo_evento)
                )
            elif sort_by == PersonaSortBy.ULTIMO_EVENTO_ASC:
                ciudadanos_query = ciudadanos_query.order_by(
                    eventos_stats_subq.c.ultimo_evento
                )

            # Paginación en SQL
            offset = (page - 1) * page_size
            ciudadanos_query = ciudadanos_query.offset(offset).limit(page_size)

            # Ejecutar query (UNA SOLA VEZ)
            result = await db.execute(ciudadanos_query)
            rows = result.all()

            # Contar total (query separada pero eficiente)
            count_query = (
                select(func.count())
                .select_from(Ciudadano)
                .outerjoin(
                    eventos_stats_subq,
                    Ciudadano.codigo_ciudadano == eventos_stats_subq.c.codigo_ciudadano,
                )
                .where(col(eventos_stats_subq.c.total_eventos).isnot(None))
            )

            if search:
                search_term = f"%{search}%"
                count_query = count_query.where(
                    or_(
                        col(Ciudadano.nombre).ilike(search_term),
                        col(Ciudadano.apellido).ilike(search_term),
                        cast(col(Ciudadano.numero_documento), String).ilike(
                            search_term
                        ),
                    )
                )

            if tiene_multiples_eventos:
                count_query = count_query.where(eventos_stats_subq.c.total_eventos > 1)

            total_result = await db.execute(count_query)
            total = total_result.scalar() or 0

            # Calcular estadísticas agregadas sobre TODAS las personas que coinciden con filtros
            # Query base para stats (reutiliza la misma lógica de filtros)
            stats_base_query = (
                select(
                    eventos_stats_subq.c.total_eventos,
                    eventos_stats_subq.c.confirmados,
                    eventos_stats_subq.c.eventos_recientes,
                )
                .select_from(Ciudadano)
                .outerjoin(
                    eventos_stats_subq,
                    Ciudadano.codigo_ciudadano == eventos_stats_subq.c.codigo_ciudadano,
                )
                .where(col(eventos_stats_subq.c.total_eventos).isnot(None))
            )

            # Aplicar los mismos filtros de búsqueda
            if search:
                search_term = f"%{search}%"
                stats_base_query = stats_base_query.where(
                    or_(
                        col(Ciudadano.nombre).ilike(search_term),
                        col(Ciudadano.apellido).ilike(search_term),
                        cast(col(Ciudadano.numero_documento), String).ilike(
                            search_term
                        ),
                    )
                )

            if tiene_multiples_eventos:
                stats_base_query = stats_base_query.where(
                    eventos_stats_subq.c.total_eventos > 1
                )

            # Ejecutar query de stats
            stats_result = await db.execute(stats_base_query)
            stats_rows = stats_result.all()

            # Calcular agregaciones
            personas_con_multiples = sum(
                1 for row in stats_rows if (row.total_eventos or 0) > 1
            )
            personas_con_confirmados = sum(
                1 for row in stats_rows if (row.confirmados or 0) > 0
            )
            personas_activas = sum(
                1 for row in stats_rows if (row.eventos_recientes or 0) > 0
            )

            # Construir respuesta desde los rows
            personas_list = []
            for row in rows:
                row_dict = row._mapping
                ciudadano = row_dict["Ciudadano"]

                personas_list.append(
                    PersonaListItem(
                        tipo_sujeto="humano",
                        persona_id=ciudadano.codigo_ciudadano,
                        nombre_completo=f"{ciudadano.nombre or ''} {ciudadano.apellido or ''}".strip()
                        or "Sin nombre",
                        documento=(
                            str(ciudadano.numero_documento)
                            if ciudadano.numero_documento
                            else None
                        ),
                        edad_actual=None,  # TODO: calcular si necesario
                        sexo=ciudadano.sexo_biologico,
                        provincia=None,  # TODO: obtener de domicilio si necesario
                        localidad=None,
                        total_eventos=row_dict["total_eventos"] or 0,
                        eventos_confirmados=row_dict["confirmados"] or 0,
                        eventos_sospechosos=row_dict["sospechosos"] or 0,
                        eventos_probables=row_dict["probables"] or 0,
                        eventos_descartados=row_dict["descartados"] or 0,
                        primer_evento_fecha=row_dict["primer_evento"],
                        ultimo_evento_fecha=row_dict["ultimo_evento"],
                        ultimo_evento_tipo=row_dict.get("ultimo_evento_tipo"),
                        ultimo_evento_clasificacion=row_dict.get(
                            "ultimo_evento_clasificacion"
                        ),
                        tiene_eventos_activos=(row_dict["eventos_recientes"] or 0) > 0,
                    )
                )

            # Respuesta con metadata de paginación y stats
            response = PersonaListResponse(
                data=personas_list,
                pagination=PaginationInfo(
                    page=page,
                    page_size=page_size,
                    total=total,
                    total_pages=(total + page_size - 1) // page_size,
                    has_next=offset + page_size < total,
                    has_prev=page > 1,
                ),
                stats=AggregatedStats(
                    total_personas=total,
                    personas_con_multiples_eventos=personas_con_multiples,
                    personas_con_confirmados=personas_con_confirmados,
                    personas_activas=personas_activas,
                ),
                filters_applied={
                    "search": search,
                    "tipo_sujeto": tipo_sujeto,
                    "provincia_ids_establecimiento_notificacion": provincia_ids_establecimiento,
                    "tipo_eno_ids": tipo_eno_ids,
                    "grupo_eno_ids": grupo_eno_ids,
                    "tiene_multiples_eventos": tiene_multiples_eventos,
                    "edad_min": edad_min,
                    "edad_max": edad_max,
                },
            )

            logger.info(f"✅ Retornando {len(personas_list)} personas de {total} total")
            return SuccessResponse(data=response)

        # TODO: Implementar animales con la misma lógica optimizada
        if buscar_animales:
            # Por ahora retornar vacío, implementar después
            return SuccessResponse(
                data=PersonaListResponse(
                    data=[],
                    pagination=PaginationInfo(
                        page=page,
                        page_size=page_size,
                        total=0,
                        total_pages=0,
                        has_next=False,
                        has_prev=False,
                    ),
                    stats=AggregatedStats(
                        total_personas=0,
                        personas_con_multiples_eventos=0,
                        personas_con_confirmados=0,
                        personas_activas=0,
                    ),
                    filters_applied={
                        "search": search,
                        "tipo_sujeto": tipo_sujeto,
                        "provincia_ids_establecimiento_notificacion": provincia_ids_establecimiento,
                        "tipo_eno_ids": tipo_eno_ids,
                        "grupo_eno_ids": grupo_eno_ids,
                        "tiene_multiples_eventos": tiene_multiples_eventos,
                        "edad_min": edad_min,
                        "edad_max": edad_max,
                    },
                )
            )

        # Fallback: retornar lista vacía si no se especificó un tipo válido
        return SuccessResponse(
            data=PersonaListResponse(
                data=[],
                pagination=PaginationInfo(
                    page=page,
                    page_size=page_size,
                    total=0,
                    total_pages=0,
                    has_next=False,
                    has_prev=False,
                ),
                stats=AggregatedStats(
                    total_personas=0,
                    personas_con_multiples_eventos=0,
                    personas_con_confirmados=0,
                    personas_activas=0,
                ),
                filters_applied={
                    "search": search,
                    "tipo_sujeto": tipo_sujeto,
                },
            )
        )
    except Exception as e:
        logger.error(f"💥 Error listando personas: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo personas: {e!s}",
        ) from e
