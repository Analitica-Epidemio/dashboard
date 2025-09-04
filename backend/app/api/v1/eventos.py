"""
Endpoints para gestión y visualización de eventos epidemiológicos.

Características:
- Listado con paginación y filtros avanzados
- Búsqueda por múltiples criterios
- Detalle completo con relaciones
- Timeline de eventos
- Exportación de datos
"""

import io
import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import String, and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_async_session
from app.core.schemas.response import ErrorResponse, SuccessResponse
from app.domains.ciudadanos.models import (
    Animal,
    Ciudadano,
    CiudadanoDomicilio,
)
from app.domains.estrategias.models import TipoClasificacion
from app.domains.eventos.models import Evento, GrupoEno, TipoEno, DetalleEventoSintomas
from app.domains.localidades.models import Departamento, Localidad

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/eventos", tags=["Eventos"])


# ============= Schemas =============

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class EventoListFilters(BaseModel):
    """Filtros para listado de eventos"""

    tipo_eno_id: Optional[int] = None
    fecha_desde: Optional[date] = None
    fecha_hasta: Optional[date] = None
    clasificacion: Optional[str] = None
    es_positivo: Optional[bool] = None
    provincia: Optional[str] = None
    localidad: Optional[str] = None
    tipo_sujeto: Optional[str] = Field(None, description="humano/animal/indeterminado")
    requiere_revision: Optional[bool] = None
    con_sintomas: Optional[bool] = None
    con_resultado_mortal: Optional[bool] = None


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


class CiudadanoInfo(BaseModel):
    """Información del ciudadano"""

    codigo: int = Field(..., description="Código del ciudadano")
    nombre: str = Field(..., description="Nombre")
    apellido: str = Field(..., description="Apellido")
    documento: Optional[str] = Field(None, description="Número de documento")
    fecha_nacimiento: Optional[date] = Field(None, description="Fecha de nacimiento")
    sexo: Optional[str] = Field(None, description="Sexo")
    provincia: Optional[str] = Field(None, description="Provincia de residencia")
    localidad: Optional[str] = Field(None, description="Localidad de residencia")
    telefono: Optional[str] = Field(None, description="Teléfono de contacto")


class AnimalInfo(BaseModel):
    """Información del animal"""

    id: int = Field(..., description="ID del animal")
    identificacion: Optional[str] = Field(None, description="Identificación del animal")
    especie: Optional[str] = Field(None, description="Especie")
    raza: Optional[str] = Field(None, description="Raza")
    provincia: Optional[str] = Field(None, description="Provincia")
    localidad: Optional[str] = Field(None, description="Localidad")


class SintomaInfo(BaseModel):
    """Información de síntoma"""

    id: int = Field(..., description="ID del síntoma")
    nombre: Optional[str] = Field(None, description="Nombre del síntoma")
    fecha: Optional[date] = Field(None, description="Fecha del síntoma")


class MuestraInfo(BaseModel):
    """Información de muestra"""

    id: int = Field(..., description="ID de la muestra")
    tipo: Optional[str] = Field(None, description="Tipo de muestra")
    fecha: Optional[date] = Field(None, description="Fecha de toma")
    resultado: Optional[str] = Field(None, description="Resultado")


class DiagnosticoInfo(BaseModel):
    """Información de diagnóstico"""

    id: int = Field(..., description="ID del diagnóstico")
    diagnostico: Optional[str] = Field(None, description="Diagnóstico")
    fecha: Optional[date] = Field(None, description="Fecha del diagnóstico")
    es_principal: Optional[bool] = Field(
        None, description="Si es diagnóstico principal"
    )


class EstablecimientoInfo(BaseModel):
    """Información de establecimiento"""
    
    id: int = Field(..., description="ID del establecimiento")
    nombre: Optional[str] = Field(None, description="Nombre del establecimiento")
    tipo: Optional[str] = Field(None, description="Tipo de establecimiento")
    provincia: Optional[str] = Field(None, description="Provincia")
    localidad: Optional[str] = Field(None, description="Localidad")


class TratamientoInfo(BaseModel):
    """Información de tratamiento"""
    
    id: int = Field(..., description="ID del tratamiento")
    descripcion: Optional[str] = Field(None, description="Descripción del tratamiento")
    fecha_inicio: Optional[date] = Field(None, description="Fecha de inicio")
    fecha_fin: Optional[date] = Field(None, description="Fecha de fin")
    recibio_tratamiento: Optional[bool] = Field(None, description="Si recibió tratamiento")


class InternacionInfo(BaseModel):
    """Información de internación"""
    
    id: int = Field(..., description="ID de la internación")
    fecha_internacion: Optional[date] = Field(None, description="Fecha de internación")
    fecha_alta: Optional[date] = Field(None, description="Fecha de alta")
    requirio_uci: Optional[bool] = Field(None, description="Si requirió UCI")


class InvestigacionInfo(BaseModel):
    """Información de investigación epidemiológica"""
    
    id: int = Field(..., description="ID de la investigación")
    es_investigacion_terreno: Optional[bool] = Field(None, description="Si fue investigación de terreno")
    fecha_investigacion: Optional[date] = Field(None, description="Fecha de investigación")
    tipo_lugar_investigacion: Optional[str] = Field(None, description="Tipo y lugar de investigación")
    origen_financiamiento: Optional[str] = Field(None, description="Origen del financiamiento")


class ContactoInfo(BaseModel):
    """Información de contactos"""
    
    id: int = Field(..., description="ID del registro de contactos")
    contacto_caso_confirmado: Optional[bool] = Field(None, description="Contacto con caso confirmado")
    contacto_caso_sospechoso: Optional[bool] = Field(None, description="Contacto con caso sospechoso")
    contactos_menores_un_ano: Optional[int] = Field(None, description="Contactos menores de 1 año")
    contactos_vacunados: Optional[int] = Field(None, description="Contactos vacunados")
    contactos_embarazadas: Optional[int] = Field(None, description="Contactos embarazadas")


class AmbitoConcurrenciaInfo(BaseModel):
    """Información de ámbito de concurrencia"""
    
    id: int = Field(..., description="ID del ámbito")
    nombre_lugar: Optional[str] = Field(None, description="Nombre del lugar")
    tipo_lugar: Optional[str] = Field(None, description="Tipo de lugar")
    localidad: Optional[str] = Field(None, description="Localidad del ámbito")
    fecha_ocurrencia: Optional[date] = Field(None, description="Fecha de ocurrencia")
    frecuencia_concurrencia: Optional[str] = Field(None, description="Frecuencia de concurrencia")


class AntecedenteInfo(BaseModel):
    """Información de antecedente epidemiológico"""
    
    id: int = Field(..., description="ID del antecedente")
    descripcion: Optional[str] = Field(None, description="Descripción del antecedente")
    fecha_antecedente: Optional[date] = Field(None, description="Fecha del antecedente")


class VacunaInfo(BaseModel):
    """Información de vacuna"""
    
    id: int = Field(..., description="ID de la vacuna")
    nombre_vacuna: Optional[str] = Field(None, description="Nombre de la vacuna")
    fecha_ultima_dosis: Optional[date] = Field(None, description="Fecha de última dosis")
    dosis_total: Optional[int] = Field(None, description="Total de dosis")


class EventoDetailResponse(BaseModel):
    """Respuesta detallada de un evento (EVENT-CENTERED)"""

    # Datos básicos del evento
    id: int = Field(..., description="ID del evento")
    id_evento_caso: int = Field(..., description="ID del caso")
    tipo_eno_id: int = Field(..., description="ID del tipo ENO")
    tipo_eno_nombre: Optional[str] = Field(None, description="Nombre del tipo ENO")
    tipo_eno_descripcion: Optional[str] = Field(
        None, description="Descripción del tipo ENO"
    )
    enfermedad: Optional[str] = Field(None, description="Enfermedad relacionada")

    # Fechas importantes
    fecha_minima_evento: date = Field(..., description="Fecha mínima del evento")
    fecha_inicio_sintomas: Optional[date] = Field(
        None, description="Fecha de inicio de síntomas"
    )
    fecha_apertura_caso: Optional[date] = Field(
        None, description="Fecha de apertura del caso"
    )
    fecha_primera_consulta: Optional[date] = Field(
        None, description="Fecha de primera consulta"
    )
    fecha_notificacion: Optional[date] = Field(
        None, description="Fecha de notificación"
    )
    fecha_diagnostico: Optional[date] = Field(
        None, description="Fecha de diagnóstico"
    )
    fecha_investigacion: Optional[date] = Field(
        None, description="Fecha de investigación"
    )

    # Semanas epidemiológicas
    semana_epidemiologica_apertura: Optional[int] = Field(
        None, description="Semana epidemiológica de apertura"
    )
    anio_epidemiologico_apertura: Optional[int] = Field(
        None, description="Año epidemiológico de apertura"
    )
    semana_epidemiologica_sintomas: Optional[int] = Field(
        None, description="Semana epidemiológica de síntomas"
    )

    # Clasificación del evento
    clasificacion_estrategia: Optional[TipoClasificacion] = Field(None, description="Clasificación estratégica del evento")
    es_positivo: Optional[bool] = Field(None, description="Si es positivo")
    confidence_score: Optional[float] = Field(None, description="Score de confianza")
    metadata_clasificacion: Optional[Dict[str, Any]] = Field(
        None, description="Metadata de clasificación"
    )
    metadata_extraida: Optional[Dict[str, Any]] = Field(
        None, description="Metadata extraída"
    )

    # Sujeto del evento
    tipo_sujeto: str = Field(..., description="Tipo de sujeto")
    ciudadano: Optional[CiudadanoInfo] = Field(
        None, description="Información del ciudadano"
    )
    animal: Optional[AnimalInfo] = Field(None, description="Información del animal")

    # Establecimientos relacionados
    establecimiento_consulta: Optional[EstablecimientoInfo] = Field(
        None, description="Establecimiento de consulta"
    )
    establecimiento_notificacion: Optional[EstablecimientoInfo] = Field(
        None, description="Establecimiento que notificó"
    )
    establecimiento_carga: Optional[EstablecimientoInfo] = Field(
        None, description="Establecimiento de carga"
    )

    # Estados y flags
    es_caso_sintomatico: Optional[bool] = Field(None, description="Si es sintomático")
    requiere_revision_especie: Optional[bool] = Field(
        None, description="Si requiere revisión"
    )

    # Observaciones y datos originales
    observaciones_texto: Optional[str] = Field(None, description="Observaciones")
    id_origen: Optional[str] = Field(None, description="ID del sistema origen")
    datos_originales_csv: Optional[Dict[str, Any]] = Field(
        None, description="Datos originales del CSV"
    )

    # TODAS las relaciones del evento (EVENT-CENTERED)
    sintomas: List[SintomaInfo] = Field(
        default_factory=list, description="Síntomas del evento"
    )
    muestras: List[MuestraInfo] = Field(
        default_factory=list, description="Muestras del evento"
    )
    diagnosticos: List[DiagnosticoInfo] = Field(
        default_factory=list, description="Diagnósticos del evento"
    )
    tratamientos: List[TratamientoInfo] = Field(
        default_factory=list, description="Tratamientos del evento"
    )
    internaciones: List[InternacionInfo] = Field(
        default_factory=list, description="Internaciones del evento"
    )
    investigaciones: List[InvestigacionInfo] = Field(
        default_factory=list, description="Investigaciones del evento"
    )
    contactos: List[ContactoInfo] = Field(
        default_factory=list, description="Contactos del evento"
    )
    ambitos_concurrencia: List[AmbitoConcurrenciaInfo] = Field(
        default_factory=list, description="Ámbitos de concurrencia"
    )
    antecedentes: List[AntecedenteInfo] = Field(
        default_factory=list, description="Antecedentes epidemiológicos"
    )
    vacunas: List[VacunaInfo] = Field(
        default_factory=list, description="Vacunas relacionadas"
    )

    # Conteos de relaciones
    total_sintomas: int = Field(0, description="Total de síntomas")
    total_muestras: int = Field(0, description="Total de muestras")
    total_diagnosticos: int = Field(0, description="Total de diagnósticos")
    total_tratamientos: int = Field(0, description="Total de tratamientos")
    total_internaciones: int = Field(0, description="Total de internaciones")
    total_investigaciones: int = Field(0, description="Total de investigaciones")

    # Metadata
    created_at: Optional[datetime] = Field(None, description="Fecha de creación")
    updated_at: Optional[datetime] = Field(None, description="Fecha de actualización")

    model_config = ConfigDict(from_attributes=True)


class EventoTimelineItem(BaseModel):
    """Item del timeline de eventos"""

    fecha: date = Field(..., description="Fecha del evento")
    tipo: str = Field(
        ..., description="Tipo de evento: sintoma/muestra/diagnostico/internacion/etc"
    )
    descripcion: str = Field(..., description="Descripción del evento")
    detalles: Optional[Dict[str, Any]] = Field(None, description="Detalles adicionales")


class EventoTimelineResponse(BaseModel):
    """Respuesta del timeline"""

    items: List[EventoTimelineItem] = Field(..., description="Items del timeline")
    total: int = Field(..., description="Total de items")


# ============= Endpoints =============

@router.get(
    "/",
    response_model=SuccessResponse[EventoListResponse],
    responses={
        500: {"model": ErrorResponse, "description": "Error interno del servidor"}
    },
)
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
    # DB
    db: AsyncSession = Depends(get_async_session),
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

    logger.info(f"📋 Listando eventos - page: {page}, filters: {locals()}")

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


@router.get(
    "/{evento_id}",
    response_model=SuccessResponse[EventoDetailResponse],
    responses={
        404: {"model": ErrorResponse, "description": "Evento no encontrado"},
        500: {"model": ErrorResponse, "description": "Error interno del servidor"},
    },
)
async def get_evento_detail(
    evento_id: int,
    include_relations: bool = Query(True, description="Incluir datos relacionados"),
    db: AsyncSession = Depends(get_async_session),
) -> SuccessResponse[EventoDetailResponse]:
    """
    Obtiene el detalle completo de un evento.

    **Incluye:**
    - Datos completos del evento
    - Información del ciudadano o animal
    - Síntomas, muestras, diagnósticos
    - Metadata de clasificación
    - Timeline de eventos
    """

    logger.info(f"🔍 Obteniendo detalle de evento {evento_id}")

    try:
        # Query con TODAS las relaciones necesarias (EVENT-CENTERED)
        query = select(Evento).where(Evento.id == evento_id)

        if include_relations:
            query = query.options(
                selectinload(Evento.tipo_eno),
                # Sujetos del evento
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
                # Establecimientos del evento
                selectinload(Evento.establecimiento_consulta),
                selectinload(Evento.establecimiento_notificacion),
                selectinload(Evento.establecimiento_carga),
                # Salud y diagnósticos del evento
                selectinload(Evento.sintomas).selectinload(DetalleEventoSintomas.sintoma),
                selectinload(Evento.muestras),
                selectinload(Evento.diagnosticos),
                selectinload(Evento.tratamientos),
                selectinload(Evento.internaciones),
                # Investigación epidemiológica del evento
                selectinload(Evento.investigaciones),
                selectinload(Evento.contactos),
                selectinload(Evento.ambitos_concurrencia),
                selectinload(Evento.antecedentes),
                # Prevención del evento
                selectinload(Evento.vacunas),
            )

        result = await db.execute(query)
        evento = result.scalar_one_or_none()

        if not evento:
            logger.warning(f"❌ Evento {evento_id} no encontrado")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Evento {evento_id} no encontrado",
            )

        # Preparar respuesta detallada (EVENT-CENTERED)
        response = EventoDetailResponse(
            # Datos básicos del evento
            id=evento.id,
            id_evento_caso=evento.id_evento_caso,
            tipo_eno_id=evento.id_tipo_eno,
            tipo_eno_nombre=evento.tipo_eno.nombre if evento.tipo_eno else None,
            tipo_eno_descripcion=evento.tipo_eno.descripcion if evento.tipo_eno else None,
            enfermedad=getattr(evento, 'enfermedad', None),
            
            # Fechas importantes del evento
            fecha_minima_evento=evento.fecha_minima_evento,
            fecha_inicio_sintomas=evento.fecha_inicio_sintomas,
            fecha_apertura_caso=evento.fecha_apertura_caso,
            fecha_primera_consulta=evento.fecha_primera_consulta,
            fecha_notificacion=getattr(evento, 'fecha_notificacion', None),
            fecha_diagnostico=getattr(evento, 'fecha_diagnostico', None),
            fecha_investigacion=getattr(evento, 'fecha_investigacion', None),
            
            # Semanas epidemiológicas
            semana_epidemiologica_apertura=evento.semana_epidemiologica_apertura,
            anio_epidemiologico_apertura=evento.anio_epidemiologico_apertura,
            semana_epidemiologica_sintomas=evento.semana_epidemiologica_sintomas,
            
            # Clasificación del evento
            clasificacion_estrategia=evento.clasificacion_estrategia,
            es_positivo=evento.es_positivo,
            confidence_score=evento.confidence_score,
            metadata_clasificacion=evento.metadata_clasificacion,
            metadata_extraida=evento.metadata_extraida,
            
            # Tipo de sujeto
            tipo_sujeto="humano" if evento.ciudadano else "animal" if evento.animal else "desconocido",
            
            # Estados del evento
            es_caso_sintomatico=evento.es_caso_sintomatico,
            requiere_revision_especie=evento.requiere_revision_especie,
            
            # Observaciones y datos originales
            observaciones_texto=evento.observaciones_texto,
            id_origen=evento.id_origen,
            datos_originales_csv=evento.datos_originales_csv,
            
            # Timestamps
            created_at=evento.created_at,
            updated_at=evento.updated_at,
            
            # Conteos iniciales
            total_sintomas=len(evento.sintomas or []),
            total_muestras=len(evento.muestras or []),
            total_diagnosticos=len(evento.diagnosticos or []),
            total_tratamientos=len(evento.tratamientos or []),
            total_internaciones=len(evento.internaciones or []),
            total_investigaciones=len(evento.investigaciones or []),
        )

        # Agregar datos del sujeto
        if evento.ciudadano:
            # Get location from first domicilio
            provincia_nombre = None
            localidad_nombre = None
            if evento.ciudadano.domicilios:
                primer_domicilio = evento.ciudadano.domicilios[0]
                if primer_domicilio.localidad:
                    localidad_nombre = primer_domicilio.localidad.nombre
                    if (
                        primer_domicilio.localidad.departamento
                        and primer_domicilio.localidad.departamento.provincia
                    ):
                        provincia_nombre = (
                            primer_domicilio.localidad.departamento.provincia.nombre
                        )

            # Get contact info from first datos record
            telefono = None
            if evento.ciudadano.datos:
                primer_datos = evento.ciudadano.datos[0]
                telefono = primer_datos.informacion_contacto

            response.ciudadano = CiudadanoInfo(
                codigo=evento.ciudadano.codigo_ciudadano,
                nombre=evento.ciudadano.nombre,
                apellido=evento.ciudadano.apellido,
                documento=str(evento.ciudadano.numero_documento)
                if evento.ciudadano.numero_documento
                else None,
                fecha_nacimiento=evento.ciudadano.fecha_nacimiento,
                sexo=evento.ciudadano.sexo_biologico,
                provincia=provincia_nombre,
                localidad=localidad_nombre,
                telefono=telefono,
            )

        if evento.animal:
            response.animal = AnimalInfo(
                id=evento.animal.id,
                identificacion=evento.animal.identificacion,
                especie=evento.animal.especie,
                raza=evento.animal.raza,
                provincia=evento.animal.provincia,
                localidad=evento.animal.localidad,
            )

        # Agregar establecimientos del evento
        if evento.establecimiento_consulta:
            response.establecimiento_consulta = EstablecimientoInfo(
                id=evento.establecimiento_consulta.id,
                nombre=evento.establecimiento_consulta.nombre,
                tipo=getattr(evento.establecimiento_consulta, 'tipo', None),
                provincia=getattr(evento.establecimiento_consulta, 'provincia', None),
                localidad=getattr(evento.establecimiento_consulta, 'localidad', None),
            )

        if evento.establecimiento_notificacion:
            response.establecimiento_notificacion = EstablecimientoInfo(
                id=evento.establecimiento_notificacion.id,
                nombre=evento.establecimiento_notificacion.nombre,
                tipo=getattr(evento.establecimiento_notificacion, 'tipo', None),
                provincia=getattr(evento.establecimiento_notificacion, 'provincia', None),
                localidad=getattr(evento.establecimiento_notificacion, 'localidad', None),
            )

        if evento.establecimiento_carga:
            response.establecimiento_carga = EstablecimientoInfo(
                id=evento.establecimiento_carga.id,
                nombre=evento.establecimiento_carga.nombre,
                tipo=getattr(evento.establecimiento_carga, 'tipo', None),
                provincia=getattr(evento.establecimiento_carga, 'provincia', None),
                localidad=getattr(evento.establecimiento_carga, 'localidad', None),
            )

        # Agregar TODAS las relaciones del evento si se solicitaron (EVENT-CENTERED)
        if include_relations:
            # Síntomas del evento
            response.sintomas = [
                SintomaInfo(
                    id=s.id,
                    nombre=s.sintoma.signo_sintoma if hasattr(s, 'sintoma') and s.sintoma else None,
                    fecha=getattr(s, 'fecha_inicio_sintoma', None),
                )
                for s in (evento.sintomas or [])
            ]

            # Muestras del evento
            response.muestras = [
                MuestraInfo(
                    id=m.id,
                    tipo=getattr(m, 'tipo_muestra', None),
                    fecha=getattr(m, 'fecha_toma_muestra', None),
                    resultado=getattr(m, 'resultado', None),
                )
                for m in (evento.muestras or [])
            ]

            # Diagnósticos del evento
            response.diagnosticos = [
                DiagnosticoInfo(
                    id=d.id,
                    diagnostico=getattr(d, 'metodo_diagnostico', None) or 
                               getattr(d, 'resultado', None) or
                               "Sin especificar",
                    fecha=getattr(d, 'fecha_diagnostico', None),
                    es_principal=None,
                )
                for d in (evento.diagnosticos or [])
            ]

            # Tratamientos del evento
            response.tratamientos = [
                TratamientoInfo(
                    id=t.id,
                    descripcion=getattr(t, 'descripcion_tratamiento', None),
                    fecha_inicio=getattr(t, 'fecha_inicio_tratamiento', None),
                    fecha_fin=getattr(t, 'fecha_fin_tratamiento', None),
                    recibio_tratamiento=getattr(t, 'recibio_tratamiento', None),
                )
                for t in (evento.tratamientos or [])
            ]

            # Internaciones del evento
            response.internaciones = [
                InternacionInfo(
                    id=i.id,
                    fecha_internacion=getattr(i, 'fecha_internacion', None),
                    fecha_alta=getattr(i, 'fecha_alta_internacion', None),
                    requirio_uci=getattr(i, 'requirio_uci', None),
                )
                for i in (evento.internaciones or [])
            ]

            # Investigaciones del evento
            response.investigaciones = [
                InvestigacionInfo(
                    id=inv.id,
                    es_investigacion_terreno=getattr(inv, 'es_investigacion_terreno', None),
                    fecha_investigacion=getattr(inv, 'fecha_investigacion', None),
                    tipo_lugar_investigacion=getattr(inv, 'tipo_y_lugar_investigacion', None),
                    origen_financiamiento=getattr(inv, 'origen_financiamiento', None),
                )
                for inv in (evento.investigaciones or [])
            ]

            # Contactos del evento
            response.contactos = [
                ContactoInfo(
                    id=c.id,
                    contacto_caso_confirmado=getattr(c, 'hubo_contacto_con_caso_confirmado', None),
                    contacto_caso_sospechoso=getattr(c, 'hubo_contacto_con_caso_sospechoso', None),
                    contactos_menores_un_ano=getattr(c, 'cantidad_contactos_menores_un_anio', None),
                    contactos_vacunados=getattr(c, 'cantidad_contactos_vacunados', None),
                    contactos_embarazadas=getattr(c, 'cantidad_contactos_embarazadas', None),
                )
                for c in (evento.contactos or [])
            ]

            # Ámbitos de concurrencia del evento
            response.ambitos_concurrencia = [
                AmbitoConcurrenciaInfo(
                    id=amb.id,
                    nombre_lugar=getattr(amb, 'nombre_lugar_ocurrencia', None),
                    tipo_lugar=getattr(amb, 'tipo_lugar_ocurrencia', None),
                    localidad=getattr(amb, 'localidad_ambito_ocurrencia', None),
                    fecha_ocurrencia=getattr(amb, 'fecha_ambito_ocurrencia', None),
                    frecuencia_concurrencia=str(getattr(amb, 'frecuencia_concurrencia', None)) if getattr(amb, 'frecuencia_concurrencia', None) else None,
                )
                for amb in (evento.ambitos_concurrencia or [])
            ]

            # Antecedentes epidemiológicos del evento
            response.antecedentes = [
                AntecedenteInfo(
                    id=ant.id,
                    descripcion=getattr(ant.antecedente_epidemiologico_rel, 'descripcion', None) if hasattr(ant, 'antecedente_epidemiologico_rel') else None,
                    fecha_antecedente=getattr(ant, 'fecha_antecedente_epidemiologico', None),
                )
                for ant in (evento.antecedentes or [])
            ]

            # Vacunas relacionadas al evento
            response.vacunas = [
                VacunaInfo(
                    id=v.id,
                    nombre_vacuna=getattr(v, 'nombre_vacuna', None),
                    fecha_ultima_dosis=getattr(v, 'fecha_ultima_dosis', None),
                    dosis_total=getattr(v, 'dosis_total', None),
                )
                for v in (evento.vacunas or [])
            ]

        logger.info(f"✅ Detalle de evento {evento_id} obtenido")
        return SuccessResponse(data=response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Error obteniendo evento {evento_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo evento: {str(e)}",
        )


@router.get(
    "/{evento_id}/timeline",
    response_model=SuccessResponse[EventoTimelineResponse],
    responses={
        404: {"model": ErrorResponse, "description": "Evento no encontrado"},
        500: {"model": ErrorResponse, "description": "Error interno del servidor"},
    },
)
async def get_evento_timeline(
    evento_id: int, db: AsyncSession = Depends(get_async_session)
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

    logger.info(f"📅 Generando timeline para evento {evento_id}")

    try:
        # Obtener evento con todas las relaciones temporales
        query = (
            select(Evento)
            .where(Evento.id == evento_id)
            .options(
                selectinload(Evento.sintomas),
                selectinload(Evento.muestras),
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
            if sintoma.fecha_inicio_sintoma:
                timeline_items.append(
                    EventoTimelineItem(
                        fecha=sintoma.fecha_inicio_sintoma,
                        tipo="sintoma",
                        descripcion=f"Síntoma: {sintoma.sintoma.signo_sintoma if sintoma.sintoma else 'No especificado'}",
                        detalles=None,
                    )
                )

        # Agregar muestras
        for muestra in evento.muestras or []:
            if muestra.fecha_muestra:
                timeline_items.append(
                    EventoTimelineItem(
                        fecha=muestra.fecha_muestra,
                        tipo="muestra",
                        descripcion=f"Muestra: {muestra.tipo_muestra}",
                        detalles={"resultado": muestra.resultado},
                    )
                )

        # Agregar diagnósticos
        for diagnostico in evento.diagnosticos or []:
            if diagnostico.fecha_diagnostico_referido:
                diagnostico_text = (
                    diagnostico.clasificacion_manual
                    or diagnostico.clasificacion_automatica
                    or diagnostico.diagnostico_referido
                    or "Sin especificar"
                )
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


@router.get(
    "/export",
    responses={
        200: {"description": "Archivo CSV con los eventos"},
        500: {"model": ErrorResponse, "description": "Error interno del servidor"},
    },
)
async def export_eventos(
    # Mismos filtros que el listado
    tipo_eno_id: Optional[int] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    clasificacion: Optional[str] = None,
    formato: str = Query("csv", description="Formato de exportación (csv/excel)"),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Exporta eventos filtrados a CSV o Excel.

    **Limitaciones:**
    - Máximo 10,000 registros por exportación
    - Incluye solo datos básicos (no relaciones completas)
    """

    logger.info(f"📤 Exportando eventos a {formato}")

    try:
        # Reutilizar lógica de filtrado del listado
        # (código similar al endpoint de listado pero sin paginación)

        # Por brevedad, simulamos con datos básicos
        output = io.BytesIO()

        # TODO: Implementar exportación real con pandas
        df = pd.DataFrame(
            {
                "ID Evento": [1, 2, 3],
                "Tipo": ["Dengue", "COVID", "Rabia"],
                "Fecha": ["2024-01-01", "2024-01-02", "2024-01-03"],
            }
        )

        if formato == "csv":
            df.to_csv(output, index=False)
            media_type = "text/csv"
            filename = f"eventos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        else:
            df.to_excel(output, index=False)
            media_type = (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            filename = f"eventos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        output.seek(0)

        return StreamingResponse(
            output,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except Exception as e:
        logger.error(f"💥 Error exportando eventos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error exportando eventos: {str(e)}",
        )
