"""
Endpoint para obtener domicilios geocodificados para visualización en mapa de puntos.

Este endpoint devuelve domicilios individuales (no agregados) con sus coordenadas,
permitiendo mostrar puntos exactos en el mapa.
"""

from datetime import date
from typing import List, Optional

from fastapi import Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlmodel import Session

from app.core.database import get_session
from app.core.schemas.response import SuccessResponse
from app.domains.eventos_epidemiologicos.eventos.models import Evento, EventoGrupoEno
from app.domains.territorio.geografia_models import Departamento, Domicilio, Localidad, Provincia


class DomicilioMapaItem(BaseModel):
    """Representa un domicilio geocodificado en el mapa"""

    id: str = Field(..., description="ID único del domicilio")
    nombre: str = Field(..., description="Dirección legible (calle + número + localidad)")
    total_eventos: int = Field(..., description="Total de eventos en este domicilio")
    latitud: float = Field(..., description="Latitud del domicilio")
    longitud: float = Field(..., description="Longitud del domicilio")

    # Datos geográficos
    id_provincia_indec: int = Field(..., description="ID INDEC de provincia")
    id_departamento_indec: Optional[int] = Field(None, description="ID INDEC de departamento")
    id_localidad_indec: int = Field(..., description="ID INDEC de localidad")
    provincia_nombre: str = Field(..., description="Nombre de provincia")
    departamento_nombre: Optional[str] = Field(None, description="Nombre de departamento")
    localidad_nombre: str = Field(..., description="Nombre de localidad")


class DomicilioMapaResponse(BaseModel):
    """Respuesta del endpoint de domicilios geocodificados"""

    items: List[DomicilioMapaItem] = Field(default_factory=list)
    total: int = Field(..., description="Total de domicilios geocodificados")
    total_eventos: int = Field(..., description="Total de eventos en todos los domicilios")


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
        1000, ge=1, le=10000, description="Máximo de domicilios a retornar"
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
        .where(Domicilio.estado_geocodificacion == "GEOCODIFICADO")
    )

    # Aplicar filtros geográficos
    if id_provincia_indec is not None:
        query = query.where(Provincia.id_provincia_indec == id_provincia_indec)
    if id_departamento_indec is not None:
        query = query.where(
            Departamento.id_departamento_indec == id_departamento_indec
        )
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

        items.append(
            DomicilioMapaItem(
                id=f"domicilio_{row.id}",
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
            )
        )

        total_eventos_global += row.total_eventos

    response_data = DomicilioMapaResponse(
        items=items, total=len(items), total_eventos=total_eventos_global
    )

    return SuccessResponse(data=response_data)
