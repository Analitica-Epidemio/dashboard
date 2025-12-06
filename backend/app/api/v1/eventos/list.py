"""
Endpoint para listado de eventos epidemiológicos.
"""

import logging
from datetime import date
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import case, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_async_session
from app.core.schemas.response import SuccessResponse
from app.core.security import RequireAnyRole
from app.domains.autenticacion.models import User
from app.domains.vigilancia_nominal.clasificacion.models import TipoClasificacion
from app.domains.vigilancia_nominal.models.enfermedad import Enfermedad
from app.domains.vigilancia_nominal.models.caso import CasoEpidemiologico
from app.domains.vigilancia_nominal.queries import CasoEpidemiologicoQueryBuilder
from app.domains.vigilancia_nominal.models.sujetos import Animal
from app.domains.vigilancia_nominal.models.sujetos import (
    Ciudadano,
)
from app.domains.territorio.geografia_models import Domicilio


class CasoEpidemiologicoSortBy(str, Enum):
    FECHA_DESC = "fecha_desc"
    FECHA_ASC = "fecha_asc"
    ID_DESC = "id_desc"
    ID_ASC = "id_asc"
    TIPO_ENO = "tipo_eno"


class CasoEpidemiologicoListItem(BaseModel):
    """Item individual en la lista de eventos"""

    id: int = Field(..., description="ID del evento")
    id_evento_caso: int = Field(..., description="ID único del caso")
    tipo_eno_id: int = Field(..., description="ID del tipo ENO")
    tipo_eno_nombre: Optional[str] = Field(None, description="Nombre del tipo ENO")
    id_domicilio: Optional[int] = Field(
        None, description="ID del domicilio asociado al evento"
    )
    fecha_minima_caso: Optional[date] = Field(None, description="Fecha del evento")
    fecha_inicio_sintomas: Optional[date] = Field(
        None, description="Fecha de inicio de síntomas"
    )
    clasificacion_estrategia: Optional[TipoClasificacion] = Field(
        None, description="Clasificación estratégica del evento"
    )
    confidence_score: Optional[float] = Field(None, description="Score de confianza")

    # Información epidemiológica
    semana_epidemiologica_apertura: Optional[int] = Field(
        None, description="Semana epidemiológica de apertura del caso"
    )
    anio_epidemiologico_apertura: Optional[int] = Field(
        None, description="Año epidemiológico de apertura del caso"
    )

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


class CasoEpidemiologicoStats(BaseModel):
    """Estadísticas agregadas de eventos"""

    total: int = Field(..., description="Total de eventos")
    confirmados: int = Field(0, description="CasoEpidemiologicos confirmados")
    sospechosos: int = Field(0, description="CasoEpidemiologicos sospechosos")
    probables: int = Field(0, description="CasoEpidemiologicos probables")
    descartados: int = Field(0, description="CasoEpidemiologicos descartados")
    negativos: int = Field(0, description="CasoEpidemiologicos negativos")
    en_estudio: int = Field(0, description="CasoEpidemiologicos en estudio")
    requiere_revision: int = Field(0, description="CasoEpidemiologicos que requieren revisión")
    sin_clasificar: int = Field(0, description="CasoEpidemiologicos sin clasificar")


class CasoEpidemiologicoListResponse(BaseModel):
    """Respuesta completa del listado de eventos"""

    data: List[CasoEpidemiologicoListItem] = Field(..., description="Lista de eventos")
    pagination: PaginationInfo = Field(..., description="Información de paginación")
    stats: CasoEpidemiologicoStats = Field(..., description="Estadísticas agregadas")
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
    tipo_eno_ids: Optional[List[int]] = Query(None, description="Lista de IDs de tipos de eventos"),
    grupo_eno_ids: Optional[List[int]] = Query(None, description="Lista de IDs de grupos de eventos"),
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    clasificacion: Optional[List[str]] = Query(None, description="Lista de clasificaciones"),
    provincia_ids_establecimiento: Optional[List[int]] = Query(
        None,
        description="Lista de códigos INDEC de provincias (filtro por ESTABLECIMIENTO DE NOTIFICACIÓN)",
        alias="provincia_id"  # Mantiene compatibilidad con frontend que usa provincia_id
    ),
    tipo_sujeto: Optional[str] = None,
    requiere_revision: Optional[bool] = None,
    edad_min: Optional[int] = Query(None, ge=0, le=120, description="Edad mínima"),
    edad_max: Optional[int] = Query(None, ge=0, le=120, description="Edad máxima"),
    # Ordenamiento
    sort_by: CasoEpidemiologicoSortBy = CasoEpidemiologicoSortBy.FECHA_DESC,
    # DB and Auth
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(RequireAnyRole()),
) -> SuccessResponse[CasoEpidemiologicoListResponse]:
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
    logger.info(f"🔍 Filtros recibidos: tipo_eno_ids={tipo_eno_ids}, grupo_eno_ids={grupo_eno_ids}, clasificacion={clasificacion}, provincia_ids_establecimiento={provincia_ids_establecimiento}")

    try:
        # Query base con JOINs y filtros usando CasoEpidemiologicoQueryBuilder
        # IMPORTANTE: Filtro de provincia se aplica por ESTABLECIMIENTO DE NOTIFICACIÓN
        query = CasoEpidemiologicoQueryBuilder.apply_filters(
            select(CasoEpidemiologico),
            tipo_eno_ids=tipo_eno_ids,
            grupo_eno_ids=grupo_eno_ids,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            clasificacion=clasificacion,
            provincia_ids_establecimiento_notificacion=provincia_ids_establecimiento,
            tipo_sujeto=tipo_sujeto,
            requiere_revision=requiere_revision,
            edad_min=edad_min,
            edad_max=edad_max,
            search=search,
        ).options(
                selectinload(CasoEpidemiologico.enfermedad),
                # Relaciones con sujetos (ciudadano/animal)
                selectinload(CasoEpidemiologico.ciudadano),
                selectinload(CasoEpidemiologico.ciudadano).selectinload(Ciudadano.datos),
                selectinload(CasoEpidemiologico.animal).selectinload(Animal.localidad),
                # Domicilio del evento (no del ciudadano!)
                selectinload(CasoEpidemiologico.domicilio).selectinload(Domicilio.localidad),
                # Relaciones con establecimientos
                selectinload(CasoEpidemiologico.establecimiento_consulta),
                selectinload(CasoEpidemiologico.establecimiento_notificacion),
                selectinload(CasoEpidemiologico.establecimiento_carga),
                # Relaciones de salud y diagnósticos
                selectinload(CasoEpidemiologico.sintomas),
                selectinload(CasoEpidemiologico.muestras),
                selectinload(CasoEpidemiologico.diagnosticos),
                selectinload(CasoEpidemiologico.internaciones),
                selectinload(CasoEpidemiologico.tratamientos),
                # Relaciones epidemiológicas
                selectinload(CasoEpidemiologico.antecedentes),
                selectinload(CasoEpidemiologico.investigaciones),
                selectinload(CasoEpidemiologico.contactos),
                selectinload(CasoEpidemiologico.ambitos_concurrencia),
                # Relaciones de prevención
                selectinload(CasoEpidemiologico.vacunas),
            )

        # Aplicar ordenamiento
        if sort_by == CasoEpidemiologicoSortBy.FECHA_DESC:
            query = query.order_by(desc(CasoEpidemiologico.fecha_minima_caso))
        elif sort_by == CasoEpidemiologicoSortBy.FECHA_ASC:
            query = query.order_by(CasoEpidemiologico.fecha_minima_caso)
        elif sort_by == CasoEpidemiologicoSortBy.ID_DESC:
            query = query.order_by(desc(CasoEpidemiologico.id_snvs))
        elif sort_by == CasoEpidemiologicoSortBy.ID_ASC:
            query = query.order_by(CasoEpidemiologico.id_snvs)
        elif sort_by == CasoEpidemiologicoSortBy.TIPO_ENO:
            query = query.order_by(Enfermedad.nombre, desc(CasoEpidemiologico.fecha_minima_caso))

        # Calcular estadísticas agregadas (usa COUNT DISTINCT para evitar duplicados de JOINs)
        # IMPORTANTE: Usa CasoEpidemiologicoQueryBuilder para consistencia con query principal
        stats_query = CasoEpidemiologicoQueryBuilder.apply_filters(
            select(
                func.count(func.distinct(CasoEpidemiologico.id)).label("total"),
                func.count(func.distinct(
                    case(
                        (CasoEpidemiologico.clasificacion_estrategia == TipoClasificacion.CONFIRMADOS, CasoEpidemiologico.id),
                        else_=None,
                    )
                )).label("confirmados"),
                func.count(func.distinct(
                    case(
                        (CasoEpidemiologico.clasificacion_estrategia == TipoClasificacion.SOSPECHOSOS, CasoEpidemiologico.id),
                        else_=None,
                    )
                )).label("sospechosos"),
                func.count(func.distinct(
                    case(
                        (CasoEpidemiologico.clasificacion_estrategia == TipoClasificacion.PROBABLES, CasoEpidemiologico.id),
                        else_=None,
                    )
                )).label("probables"),
                func.count(func.distinct(
                    case(
                        (CasoEpidemiologico.clasificacion_estrategia == TipoClasificacion.DESCARTADOS, CasoEpidemiologico.id),
                        else_=None,
                    )
                )).label("descartados"),
                func.count(func.distinct(
                    case(
                        (CasoEpidemiologico.clasificacion_estrategia == TipoClasificacion.NEGATIVOS, CasoEpidemiologico.id),
                        else_=None,
                    )
                )).label("negativos"),
                func.count(func.distinct(
                    case(
                        (CasoEpidemiologico.clasificacion_estrategia == TipoClasificacion.EN_ESTUDIO, CasoEpidemiologico.id),
                        else_=None,
                    )
                )).label("en_estudio"),
                func.count(func.distinct(
                    case(
                        (CasoEpidemiologico.clasificacion_estrategia == TipoClasificacion.REQUIERE_REVISION, CasoEpidemiologico.id),
                        else_=None,
                    )
                )).label("requiere_revision"),
                func.count(func.distinct(
                    case(
                        (CasoEpidemiologico.clasificacion_estrategia.is_(None), CasoEpidemiologico.id),
                        else_=None,
                    )
                )).label("sin_clasificar"),
            ).select_from(CasoEpidemiologico),
            tipo_eno_ids=tipo_eno_ids,
            grupo_eno_ids=grupo_eno_ids,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            clasificacion=clasificacion,
            provincia_ids_establecimiento_notificacion=provincia_ids_establecimiento,
            tipo_sujeto=tipo_sujeto,
            requiere_revision=requiere_revision,
            edad_min=edad_min,
            edad_max=edad_max,
            search=search,
        )

        stats_result = await db.execute(stats_query)
        stats_row = stats_result.one()

        stats = CasoEpidemiologicoStats(
            total=stats_row.total or 0,
            confirmados=stats_row.confirmados or 0,
            sospechosos=stats_row.sospechosos or 0,
            probables=stats_row.probables or 0,
            descartados=stats_row.descartados or 0,
            negativos=stats_row.negativos or 0,
            en_estudio=stats_row.en_estudio or 0,
            requiere_revision=stats_row.requiere_revision or 0,
            sin_clasificar=stats_row.sin_clasificar or 0,
        )

        logger.info(f"📊 Stats calculadas: total={stats.total}, confirmados={stats.confirmados}, sospechosos={stats.sospechosos}, descartados={stats.descartados}")

        # Si hay filtro de grupos, necesitamos usar DISTINCT pero no podemos por las columnas JSON
        # Solución: primero obtener IDs únicos, luego cargar los eventos completos
        if grupo_eno_ids:
            # Subquery para obtener solo IDs distintos
            # IMPORTANTE: Usa CasoEpidemiologicoQueryBuilder para consistencia con query principal
            ids_subquery = CasoEpidemiologicoQueryBuilder.apply_filters(
                select(CasoEpidemiologico.id.distinct()),
                tipo_eno_ids=tipo_eno_ids,
                grupo_eno_ids=grupo_eno_ids,
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
                clasificacion=clasificacion,
                provincia_ids_establecimiento_notificacion=provincia_ids_establecimiento,
                tipo_sujeto=tipo_sujeto,
                requiere_revision=requiere_revision,
                edad_min=edad_min,
                edad_max=edad_max,
                search=search,
            )

            # Obtener los IDs
            offset = (page - 1) * page_size
            ids_result = await db.execute(ids_subquery.offset(offset).limit(page_size))
            evento_ids = [row[0] for row in ids_result.all()]

            logger.info(f"📍 IDs únicos obtenidos para página {page}: {len(evento_ids)} (offset={offset}, limit={page_size})")

            if evento_ids:
                # Ahora cargar eventos completos con esos IDs
                # Recrear query sin los joins que causan duplicados
                query = (
                    select(CasoEpidemiologico)
                    .where(CasoEpidemiologico.id.in_(evento_ids))
                    .options(
                        selectinload(CasoEpidemiologico.enfermedad),
                        selectinload(CasoEpidemiologico.ciudadano),
                        selectinload(CasoEpidemiologico.ciudadano).selectinload(Ciudadano.datos),
                        selectinload(CasoEpidemiologico.animal).selectinload(Animal.localidad),
                        # Domicilio del evento (no del ciudadano!)
                        selectinload(CasoEpidemiologico.domicilio).selectinload(Domicilio.localidad),
                        selectinload(CasoEpidemiologico.establecimiento_consulta),
                        selectinload(CasoEpidemiologico.establecimiento_notificacion),
                        selectinload(CasoEpidemiologico.establecimiento_carga),
                        selectinload(CasoEpidemiologico.sintomas),
                        selectinload(CasoEpidemiologico.muestras),
                        selectinload(CasoEpidemiologico.diagnosticos),
                        selectinload(CasoEpidemiologico.internaciones),
                        selectinload(CasoEpidemiologico.tratamientos),
                        selectinload(CasoEpidemiologico.antecedentes),
                        selectinload(CasoEpidemiologico.investigaciones),
                        selectinload(CasoEpidemiologico.contactos),
                        selectinload(CasoEpidemiologico.ambitos_concurrencia),
                        selectinload(CasoEpidemiologico.vacunas),
                    )
                )

                # Aplicar mismo ordenamiento
                if sort_by == CasoEpidemiologicoSortBy.FECHA_DESC:
                    query = query.order_by(desc(CasoEpidemiologico.fecha_minima_caso))
                elif sort_by == CasoEpidemiologicoSortBy.FECHA_ASC:
                    query = query.order_by(CasoEpidemiologico.fecha_minima_caso)
                elif sort_by == CasoEpidemiologicoSortBy.ID_DESC:
                    query = query.order_by(desc(CasoEpidemiologico.id_snvs))
                elif sort_by == CasoEpidemiologicoSortBy.ID_ASC:
                    query = query.order_by(CasoEpidemiologico.id_snvs)
                elif sort_by == CasoEpidemiologicoSortBy.TIPO_ENO:
                    query = query.join(Enfermedad, CasoEpidemiologico.id_enfermedad == Enfermedad.id).order_by(
                        Enfermedad.nombre, desc(CasoEpidemiologico.fecha_minima_caso)
                    )

                result = await db.execute(query)
                eventos = result.scalars().all()
            else:
                eventos = []
        else:
            # Sin filtro de grupos, usar query normal (sin DISTINCT)
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)

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
                # Calcular edad a partir de fecha_nacimiento y fecha_apertura_caso
                edad = None
                if evento.fecha_nacimiento and evento.fecha_apertura_caso:
                    edad = (evento.fecha_apertura_caso - evento.fecha_nacimiento).days // 365
                sexo = evento.ciudadano.sexo_biologico

                # Get location from evento domicilio (not ciudadano!)
                if evento.domicilio and evento.domicilio.localidad:
                    localidad_res = evento.domicilio.localidad.nombre
                else:
                    localidad_res = None
            elif evento.animal:
                tipo_sujeto = "animal"
                nombre_sujeto = (
                    evento.animal.identificacion
                    or f"{evento.animal.especie} #{evento.animal.id}"
                )

                # Get location from animal's localidad
                if evento.animal.localidad:
                    localidad_res = evento.animal.localidad.nombre
                else:
                    localidad_res = None

            eventos_list.append(
                CasoEpidemiologicoListItem(
                    id=evento.id,
                    id_evento_caso=evento.id_snvs,
                    tipo_eno_id=evento.id_enfermedad,
                    tipo_eno_nombre=evento.enfermedad.nombre if evento.enfermedad else None,
                    id_domicilio=evento.id_domicilio,
                    fecha_minima_caso=evento.fecha_minima_caso,
                    fecha_inicio_sintomas=evento.fecha_inicio_sintomas,
                    clasificacion_estrategia=evento.clasificacion_estrategia,
                    confidence_score=evento.confidence_score,
                    semana_epidemiologica_apertura=evento.semana_epidemiologica_apertura,
                    anio_epidemiologico_apertura=evento.anio_epidemiologico_apertura,
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
                        any(d.es_fallecido for d in (evento.internaciones or []))
                    ),
                    cantidad_sintomas=len(evento.sintomas or []),
                    cantidad_muestras=len(evento.muestras or []),
                    cantidad_diagnosticos=len(evento.diagnosticos or []),
                )
            )

        # Respuesta con metadata de paginación
        response = CasoEpidemiologicoListResponse(
            data=eventos_list,
            pagination=PaginationInfo(
                page=page,
                page_size=page_size,
                total=stats.total,
                total_pages=(stats.total + page_size - 1) // page_size,
                has_next=page * page_size < stats.total,
                has_prev=page > 1,
            ),
            stats=stats,
            filters_applied={
                "search": search,
                "tipo_eno_ids": tipo_eno_ids,
                "grupo_eno_ids": grupo_eno_ids,
                "fecha_desde": fecha_desde,
                "fecha_hasta": fecha_hasta,
                "clasificacion": clasificacion,
                "provincia_ids_establecimiento_notificacion": provincia_ids_establecimiento,
                "tipo_sujeto": tipo_sujeto,
                "requiere_revision": requiere_revision,
                "edad_min": edad_min,
                "edad_max": edad_max,
            },
        )

        logger.info(f"✅ Encontrados {len(eventos_list)} eventos de {stats.total} total")
        return SuccessResponse(data=response)

    except Exception as e:
        logger.error(f"💥 Error listando eventos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo eventos: {str(e)}",
        )
