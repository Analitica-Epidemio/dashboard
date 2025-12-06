"""
Endpoint para obtener establecimientos de salud geocodificados para visualización en mapa.
"""

from typing import List, Optional

from fastapi import Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlmodel import Session, col

from app.core.database import get_session
from app.core.schemas.response import SuccessResponse
from app.domains.territorio.establecimientos_models import Establecimiento
from app.domains.territorio.geografia_models import Departamento, Localidad, Provincia


class EstablecimientoMapaItem(BaseModel):
    """Item de establecimiento para mostrar en el mapa"""

    id: int = Field(..., description="ID del establecimiento")
    codigo_refes: Optional[str] = Field(None, description="Código REFES/IGN")
    nombre: str = Field(..., description="Nombre del establecimiento")
    latitud: float = Field(..., description="Latitud")
    longitud: float = Field(..., description="Longitud")

    # Datos geográficos
    id_localidad_indec: Optional[int] = Field(None, description="ID INDEC localidad")
    localidad_nombre: Optional[str] = Field(None, description="Nombre de la localidad")
    departamento_nombre: Optional[str] = Field(
        None, description="Nombre del departamento"
    )
    provincia_nombre: Optional[str] = Field(None, description="Nombre de la provincia")


class EstablecimientosMapaResponse(BaseModel):
    """Respuesta con lista de establecimientos para mapa"""

    items: List[EstablecimientoMapaItem] = Field(
        default_factory=list, description="Lista de establecimientos"
    )
    total: int = Field(..., description="Total de establecimientos")


async def get_establecimientos_mapa(
    id_provincia_indec: Optional[int] = Query(
        None, description="Filtrar por provincia"
    ),
    id_departamento_indec: Optional[int] = Query(
        None, description="Filtrar por departamento"
    ),
    id_localidad_indec: Optional[int] = Query(
        None, description="Filtrar por localidad"
    ),
    limit: Optional[int] = Query(10000, description="Límite de resultados", le=50000),
    session: Session = Depends(get_session),
) -> SuccessResponse[EstablecimientosMapaResponse]:
    """
    Obtiene establecimientos de salud geocodificados para mostrar en el mapa.

    Solo retorna establecimientos con coordenadas válidas.
    Permite filtrar por ubicación geográfica.
    """

    # Query base: solo establecimientos con coordenadas
    query = (
        select(
            col(Establecimiento.id),
            col(Establecimiento.codigo_refes),
            col(Establecimiento.nombre),
            col(Establecimiento.latitud),
            col(Establecimiento.longitud),
            col(Establecimiento.id_localidad_indec),
            col(Localidad.nombre).label("localidad_nombre"),
            col(Departamento.nombre).label("departamento_nombre"),
            col(Provincia.nombre).label("provincia_nombre"),
        )
        .select_from(Establecimiento)
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
            col(Departamento.id_provincia_indec) == col(Provincia.id_provincia_indec),
        )
        .where(col(Establecimiento.latitud).isnot(None))
        .where(col(Establecimiento.longitud).isnot(None))
    )

    # Aplicar filtros geográficos
    if id_provincia_indec is not None:
        query = query.where(col(Provincia.id_provincia_indec) == id_provincia_indec)

    if id_departamento_indec is not None:
        query = query.where(
            col(Departamento.id_departamento_indec) == id_departamento_indec
        )

    if id_localidad_indec is not None:
        query = query.where(col(Localidad.id_localidad_indec) == id_localidad_indec)

    # Limitar resultados
    if limit:
        query = query.limit(limit)

    # Ejecutar query
    results = session.execute(query).all()

    # Construir items
    items = [
        EstablecimientoMapaItem(
            id=row.id,
            codigo_refes=row.codigo_refes,
            nombre=row.nombre,
            latitud=row.latitud,
            longitud=row.longitud,
            id_localidad_indec=row.id_localidad_indec,
            localidad_nombre=row.localidad_nombre,
            departamento_nombre=row.departamento_nombre,
            provincia_nombre=row.provincia_nombre,
        )
        for row in results
    ]

    response_data = EstablecimientosMapaResponse(items=items, total=len(items))

    return SuccessResponse(data=response_data)
