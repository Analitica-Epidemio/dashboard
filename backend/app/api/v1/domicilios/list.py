"""
Endpoint para listar domicilios con información de eventos.

Permite ver todos los domicilios ordenados por cantidad de eventos,
con información de estado de geocodificación y localización.
"""

from typing import List, Optional

from fastapi import Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlmodel import Session

from app.core.database import get_session
from app.core.schemas.response import SuccessResponse
from app.domains.vigilancia_nominal.models.caso import CasoEpidemiologico
from app.domains.territorio.geografia_models import (
    Departamento,
    Domicilio,
    EstadoGeocodificacion,
    Localidad,
    Provincia,
)


class DomicilioListItem(BaseModel):
    """Item de domicilio en la lista"""

    id: int = Field(..., description="ID del domicilio")
    calle: Optional[str] = Field(None, description="Nombre de la calle")
    numero: Optional[str] = Field(None, description="Número de calle")
    direccion_completa: str = Field(..., description="Dirección completa formateada")

    # Información geográfica
    id_localidad_indec: int = Field(..., description="ID INDEC de localidad")
    localidad_nombre: str = Field(..., description="Nombre de la localidad")
    id_departamento_indec: Optional[int] = Field(
        None, description="ID INDEC del departamento"
    )
    departamento_nombre: Optional[str] = Field(None, description="Nombre del departamento")
    id_provincia_indec: int = Field(..., description="ID INDEC de provincia")
    provincia_nombre: str = Field(..., description="Nombre de la provincia")

    # Coordenadas
    latitud: Optional[float] = Field(None, description="Latitud")
    longitud: Optional[float] = Field(None, description="Longitud")

    # Estado de geocodificación
    estado_geocodificacion: str = Field(..., description="Estado de geocodificación")
    proveedor_geocoding: Optional[str] = Field(
        None, description="Proveedor de geocodificación"
    )
    confidence_geocoding: Optional[float] = Field(
        None, description="Confianza de geocodificación (0-1)"
    )

    # Estadísticas de eventos
    total_eventos: int = Field(default=0, description="Total de eventos en este domicilio")


class DomiciliosListResponse(BaseModel):
    """Respuesta paginada de domicilios"""

    items: List[DomicilioListItem] = Field(default_factory=list)
    total: int = Field(..., description="Total de domicilios")
    page: int = Field(..., description="Página actual")
    page_size: int = Field(..., description="Tamaño de página")
    total_pages: int = Field(..., description="Total de páginas")


async def list_domicilios(
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(50, ge=1, le=500, description="Tamaño de página"),
    estado_geocodificacion: Optional[EstadoGeocodificacion] = Query(
        None, description="Filtrar por estado de geocodificación"
    ),
    id_provincia_indec: Optional[int] = Query(
        None, description="Filtrar por provincia"
    ),
    id_departamento_indec: Optional[int] = Query(
        None, description="Filtrar por departamento"
    ),
    id_localidad_indec: Optional[int] = Query(
        None, description="Filtrar por localidad"
    ),
    con_eventos: Optional[bool] = Query(
        None, description="Filtrar solo domicilios con eventos (true) o sin eventos (false)"
    ),
    order_by: str = Query(
        "eventos_desc",
        description="Ordenamiento: eventos_desc, eventos_asc, calle_asc, localidad_asc",
    ),
    session: Session = Depends(get_session),
) -> SuccessResponse[DomiciliosListResponse]:
    """
    Lista domicilios con información de eventos y geocodificación.

    Por defecto ordena por cantidad de eventos descendente (hotspots primero).
    """

    # Subquery para contar eventos por domicilio
    eventos_count_subquery = (
        select(
            CasoEpidemiologico.id_domicilio,
            func.count(CasoEpidemiologico.id).label("total_eventos"),
        )
        .where(CasoEpidemiologico.id_domicilio.is_not(None))
        .group_by(CasoEpidemiologico.id_domicilio)
        .subquery()
    )

    # Query principal
    query = (
        select(
            Domicilio.id,
            Domicilio.calle,
            Domicilio.numero,
            Domicilio.latitud,
            Domicilio.longitud,
            Domicilio.estado_geocodificacion,
            Domicilio.proveedor_geocoding,
            Domicilio.confidence_geocoding,
            Domicilio.id_localidad_indec,
            Localidad.nombre.label("localidad_nombre"),
            Departamento.id_departamento_indec,
            Departamento.nombre.label("departamento_nombre"),
            Provincia.id_provincia_indec,
            Provincia.nombre.label("provincia_nombre"),
            func.coalesce(eventos_count_subquery.c.total_eventos, 0).label(
                "total_eventos"
            ),
        )
        .select_from(Domicilio)
        .join(Localidad, Domicilio.id_localidad_indec == Localidad.id_localidad_indec)
        .join(
            Departamento,
            Localidad.id_departamento_indec == Departamento.id_departamento_indec,
        )
        .join(
            Provincia, Departamento.id_provincia_indec == Provincia.id_provincia_indec
        )
        .outerjoin(
            eventos_count_subquery,
            Domicilio.id == eventos_count_subquery.c.id_domicilio,
        )
    )

    # Aplicar filtros
    if estado_geocodificacion is not None:
        query = query.where(Domicilio.estado_geocodificacion == estado_geocodificacion)

    if id_provincia_indec is not None:
        query = query.where(Provincia.id_provincia_indec == id_provincia_indec)

    if id_departamento_indec is not None:
        query = query.where(Departamento.id_departamento_indec == id_departamento_indec)

    if id_localidad_indec is not None:
        query = query.where(Localidad.id_localidad_indec == id_localidad_indec)

    if con_eventos is not None:
        if con_eventos:
            query = query.where(eventos_count_subquery.c.total_eventos > 0)
        else:
            query = query.where(
                func.coalesce(eventos_count_subquery.c.total_eventos, 0) == 0
            )

    # Contar total (usar scalar_one para obtener el valor directamente)
    count_query = select(func.count()).select_from(query.subquery())
    total = session.execute(count_query).scalar_one()

    # Aplicar ordenamiento
    if order_by == "eventos_desc":
        query = query.order_by(
            func.coalesce(eventos_count_subquery.c.total_eventos, 0).desc()
        )
    elif order_by == "eventos_asc":
        query = query.order_by(
            func.coalesce(eventos_count_subquery.c.total_eventos, 0).asc()
        )
    elif order_by == "calle_asc":
        query = query.order_by(Domicilio.calle.asc())
    elif order_by == "localidad_asc":
        query = query.order_by(Localidad.nombre.asc(), Domicilio.calle.asc())

    # Aplicar paginación
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Ejecutar query
    results = session.exec(query).all()

    # Construir items
    items: List[DomicilioListItem] = []
    for row in results:
        # Construir dirección completa
        partes_direccion = []
        if row.calle:
            direccion_calle = row.calle
            if row.numero:
                direccion_calle += f" {row.numero}"
            partes_direccion.append(direccion_calle)
        partes_direccion.append(row.localidad_nombre)
        if row.departamento_nombre:
            partes_direccion.append(row.departamento_nombre)
        partes_direccion.append(row.provincia_nombre)

        direccion_completa = ", ".join(partes_direccion)

        items.append(
            DomicilioListItem(
                id=row.id,
                calle=row.calle,
                numero=row.numero,
                direccion_completa=direccion_completa,
                id_localidad_indec=row.id_localidad_indec,
                localidad_nombre=row.localidad_nombre,
                id_departamento_indec=row.id_departamento_indec,
                departamento_nombre=row.departamento_nombre,
                id_provincia_indec=row.id_provincia_indec,
                provincia_nombre=row.provincia_nombre,
                latitud=float(row.latitud) if row.latitud else None,
                longitud=float(row.longitud) if row.longitud else None,
                estado_geocodificacion=row.estado_geocodificacion.value,
                proveedor_geocoding=row.proveedor_geocoding,
                confidence_geocoding=row.confidence_geocoding,
                total_eventos=row.total_eventos,
            )
        )

    # Calcular total de páginas
    total_pages = (total + page_size - 1) // page_size

    response_data = DomiciliosListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )

    return SuccessResponse(data=response_data)
