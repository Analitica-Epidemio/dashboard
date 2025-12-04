"""
Endpoint para obtener domicilios geocodificados para visualización en mapa de puntos.

Este endpoint devuelve domicilios individuales (no agregados) con sus coordenadas,
permitiendo mostrar puntos exactos en el mapa.
"""

import logging
from datetime import date
from typing import List, Optional

from fastapi import Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlmodel import Session

from app.core.database import get_session
from app.core.schemas.response import SuccessResponse
from app.domains.eventos_epidemiologicos.eventos.models import (
    Evento,
    EventoGrupoEno,
    TipoEno,
)
from app.domains.territorio.geografia_models import (
    Departamento,
    Domicilio,
    EstadoGeocodificacion,
    Localidad,
    Provincia,
)

logger = logging.getLogger(__name__)


class DomicilioMapaItem(BaseModel):
    """Representa un domicilio geocodificado en el mapa"""

    id: str = Field(..., description="ID único del domicilio")
    id_domicilio: int = Field(..., description="ID numérico del domicilio")
    nombre: str = Field(
        ..., description="Dirección legible (calle + número + localidad)"
    )
    total_eventos: int = Field(..., description="Total de eventos en este domicilio")
    latitud: float = Field(..., description="Latitud del domicilio")
    longitud: float = Field(..., description="Longitud del domicilio")

    # Datos geográficos
    id_provincia_indec: int = Field(..., description="ID INDEC de provincia")
    id_departamento_indec: Optional[int] = Field(
        None, description="ID INDEC de departamento"
    )
    id_localidad_indec: int = Field(..., description="ID INDEC de localidad")
    provincia_nombre: str = Field(..., description="Nombre de provincia")
    departamento_nombre: Optional[str] = Field(
        None, description="Nombre de departamento"
    )
    localidad_nombre: str = Field(..., description="Nombre de localidad")

    # Datos de tipos de evento (para colorear markers)
    tipo_evento_predominante: Optional[str] = Field(
        None, description="Tipo de evento más frecuente"
    )
    tipos_eventos: dict = Field(
        default_factory=dict, description="Conteo por tipo de evento"
    )
    primer_evento_fecha: Optional[date] = Field(
        None, description="Fecha del primer evento registrado en el domicilio"
    )

    # Fechas de todos los eventos para animación temporal
    # Lista de fechas (fecha_inicio_sintomas o fecha_minima_evento) para timeline
    fechas_eventos: List[date] = Field(
        default_factory=list,
        description="Lista de fechas de eventos para animación temporal"
    )


class DomicilioMapaResponse(BaseModel):
    """Respuesta del endpoint de domicilios geocodificados"""

    items: List[DomicilioMapaItem] = Field(default_factory=list)
    total: int = Field(..., description="Total de domicilios geocodificados")
    total_eventos: int = Field(
        ..., description="Total de eventos en todos los domicilios"
    )


async def get_domicilios_mapa(
    id_provincia_indec: Optional[int] = Query(
        None, description="Filtrar por provincia"
    ),
    id_departamento_indec: Optional[int] = Query(
        None, description="Filtrar por departamento"
    ),
    id_localidad_indec: Optional[int] = Query(
        None, description="Filtrar por localidad"
    ),
    id_grupo_eno: Optional[int] = Query(None, description="Filtrar por grupo ENO"),
    id_tipo_eno: Optional[int] = Query(None, description="Filtrar por tipo ENO"),
    fecha_hasta: Optional[date] = Query(
        None, description="Filtrar eventos hasta esta fecha"
    ),
    limit: int = Query(
        50000, ge=1, le=100000, description="Máximo de domicilios a retornar"
    ),
    session: Session = Depends(get_session),
) -> SuccessResponse[DomicilioMapaResponse]:
    """
    Obtiene domicilios geocodificados con conteo de eventos.

    Retorna solo domicilios que tienen:
    - Coordenadas geocodificadas (latitud y longitud no NULL)
    - Al menos un evento asociado

    Útil para visualización de mapa de puntos coloreados por provincia.
    """

    logger.debug(
        "Obteniendo domicilios geocodificados para mapa | filtros provincia=%s depto=%s "
        "localidad=%s grupo_eno=%s tipo_eno=%s fecha_hasta=%s limit=%s",
        id_provincia_indec,
        id_departamento_indec,
        id_localidad_indec,
        id_grupo_eno,
        id_tipo_eno,
        fecha_hasta,
        limit,
    )

    # Query principal: agrupar eventos por domicilio geocodificado
    query = (
        select(
            Domicilio.id,
            Domicilio.calle,
            Domicilio.numero,
            Domicilio.latitud,
            Domicilio.longitud,
            Localidad.id_localidad_indec,
            Localidad.nombre.label("localidad_nombre"),
            Departamento.id_departamento_indec,
            Departamento.nombre.label("departamento_nombre"),
            Provincia.id_provincia_indec,
            Provincia.nombre.label("provincia_nombre"),
            func.count(Evento.id).label("total_eventos"),
            func.min(Evento.fecha_minima_evento).label("primer_evento_fecha"),
        )
        .select_from(Evento)
        .join(Domicilio, Evento.id_domicilio == Domicilio.id)
        .join(Localidad, Domicilio.id_localidad_indec == Localidad.id_localidad_indec)
        .join(
            Departamento,
            Localidad.id_departamento_indec == Departamento.id_departamento_indec,
        )
        .join(
            Provincia, Departamento.id_provincia_indec == Provincia.id_provincia_indec
        )
        # Solo domicilios geocodificados exitosamente
        .where(Domicilio.latitud.is_not(None))
        .where(Domicilio.longitud.is_not(None))
        .where(Domicilio.estado_geocodificacion == EstadoGeocodificacion.GEOCODIFICADO)
    )

    # Aplicar filtros geográficos
    if id_provincia_indec is not None:
        query = query.where(Provincia.id_provincia_indec == id_provincia_indec)
    if id_departamento_indec is not None:
        query = query.where(Departamento.id_departamento_indec == id_departamento_indec)
    if id_localidad_indec is not None:
        query = query.where(Localidad.id_localidad_indec == id_localidad_indec)

    # Aplicar filtros de tipo de evento
    if id_grupo_eno is not None:
        query = query.where(
            Evento.id.in_(
                select(EventoGrupoEno.id_evento).where(
                    EventoGrupoEno.id_grupo_eno == id_grupo_eno
                )
            )
        )
    if id_tipo_eno is not None:
        query = query.where(Evento.id_tipo_eno == id_tipo_eno)

    # Filtro temporal
    if fecha_hasta is not None:
        query = query.where(Evento.fecha_minima_evento <= fecha_hasta)

    # Agrupar por domicilio
    query = query.group_by(
        Domicilio.id,
        Domicilio.calle,
        Domicilio.numero,
        Domicilio.latitud,
        Domicilio.longitud,
        Localidad.id_localidad_indec,
        Localidad.nombre,
        Departamento.id_departamento_indec,
        Departamento.nombre,
        Provincia.id_provincia_indec,
        Provincia.nombre,
    )

    # Ordenar por cantidad de eventos (priorizar hotspots) y limitar
    query = query.order_by(func.count(Evento.id).desc()).limit(limit)

    result = session.exec(query).all()

    if not result:
        logger.info(
            "No se encontraron domicilios geocodificados con eventos usando los filtros dados"
        )
    else:
        logger.debug(
            "Query de domicilios mapa retornó %s domicilios y %s eventos totales (parcial)",
            len(result),
            sum(row.total_eventos for row in result),
        )

    # Obtener tipos de evento por domicilio para todos los domicilios retornados
    domicilio_ids = [row.id for row in result]
    tipos_por_domicilio = {}

    if domicilio_ids:
        # Query para obtener conteo de tipos por domicilio
        tipos_query = (
            select(
                Evento.id_domicilio,
                TipoEno.nombre.label("tipo_nombre"),
                func.count(Evento.id).label("count"),
            )
            .select_from(Evento)
            .outerjoin(TipoEno, Evento.id_tipo_eno == TipoEno.id)
            .where(Evento.id_domicilio.in_(domicilio_ids))
            .group_by(Evento.id_domicilio, TipoEno.nombre)
        )

        tipos_result = session.exec(tipos_query).all()

        # Organizar por domicilio
        for tipo_row in tipos_result:
            dom_id = tipo_row.id_domicilio
            tipo_nombre = tipo_row.tipo_nombre or "Sin clasificar"
            count = tipo_row.count

            if dom_id not in tipos_por_domicilio:
                tipos_por_domicilio[dom_id] = {}

            tipos_por_domicilio[dom_id][tipo_nombre] = count

    # Query para obtener fechas de eventos por domicilio (para animación temporal)
    fechas_por_domicilio: dict[int, List[date]] = {}

    if domicilio_ids:
        # Obtener fecha_minima_evento de cada evento por domicilio
        fechas_query = (
            select(
                Evento.id_domicilio,
                Evento.fecha_minima_evento,
            )
            .where(Evento.id_domicilio.in_(domicilio_ids))
            .where(Evento.fecha_minima_evento.is_not(None))
        )

        fechas_result = session.exec(fechas_query).all()

        # Organizar fechas por domicilio
        for fecha_row in fechas_result:
            dom_id = fecha_row.id_domicilio
            fecha = fecha_row.fecha_minima_evento

            if dom_id not in fechas_por_domicilio:
                fechas_por_domicilio[dom_id] = []

            fechas_por_domicilio[dom_id].append(fecha)

    # Construir items
    items: List[DomicilioMapaItem] = []
    total_eventos_global = 0

    for row in result:
        # Construir dirección legible
        partes_direccion = []
        if row.calle:
            direccion = row.calle
            if row.numero:
                direccion += f" {row.numero}"
            partes_direccion.append(direccion)
        partes_direccion.append(row.localidad_nombre)

        nombre = ", ".join(partes_direccion)

        # Obtener tipos para este domicilio
        tipos_dict = tipos_por_domicilio.get(row.id, {})
        tipo_predominante = None
        if tipos_dict:
            # Encontrar el tipo con más casos
            tipo_predominante = max(tipos_dict.items(), key=lambda x: x[1])[0]

        # Obtener fechas para este domicilio (ordenadas)
        fechas_dom = sorted(fechas_por_domicilio.get(row.id, []))

        items.append(
            DomicilioMapaItem(
                id=f"domicilio_{row.id}",
                id_domicilio=row.id,
                nombre=nombre,
                total_eventos=row.total_eventos,
                latitud=float(row.latitud),
                longitud=float(row.longitud),
                id_provincia_indec=row.id_provincia_indec,
                id_departamento_indec=row.id_departamento_indec,
                id_localidad_indec=row.id_localidad_indec,
                provincia_nombre=row.provincia_nombre,
                departamento_nombre=row.departamento_nombre,
                localidad_nombre=row.localidad_nombre,
                tipo_evento_predominante=tipo_predominante,
                tipos_eventos=tipos_dict,
                primer_evento_fecha=row.primer_evento_fecha,
                fechas_eventos=fechas_dom,
            )
        )

        total_eventos_global += row.total_eventos

    response_data = DomicilioMapaResponse(
        items=items, total=len(items), total_eventos=total_eventos_global
    )

    return SuccessResponse(data=response_data)
