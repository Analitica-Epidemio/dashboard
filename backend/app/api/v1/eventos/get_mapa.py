"""
Endpoint para obtener datos de eventos agrupados geográficamente para el mapa.
"""

from typing import List, Literal, Optional

from fastapi import Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlmodel import Session

from app.core.database import get_session
from app.core.schemas.response import SuccessResponse
from app.domains.eventos_epidemiologicos.eventos.models import Evento, EventoGrupoEno, GrupoEno, TipoEno
from app.domains.territorio.geografia_models import Departamento, Domicilio, Localidad, Provincia


class EventoMapaItem(BaseModel):
    """Representa un punto o área en el mapa con eventos agregados"""

    id: str = Field(..., description="ID único del punto (provincia_id, departamento_id o localidad_id)")
    nombre: str = Field(..., description="Nombre de la ubicación")
    nivel: Literal["provincia", "departamento", "localidad"] = Field(
        ..., description="Nivel geográfico"
    )
    total_eventos: int = Field(..., description="Total de eventos en esta ubicación")
    latitud: Optional[float] = Field(None, description="Latitud del centroide o primera ubicación")
    longitud: Optional[float] = Field(None, description="Longitud del centroide o primera ubicación")

    # Datos adicionales según nivel
    id_provincia_indec: Optional[int] = Field(None, description="ID INDEC de provincia")
    id_departamento_indec: Optional[int] = Field(None, description="ID INDEC de departamento")
    id_localidad_indec: Optional[int] = Field(None, description="ID INDEC de localidad")
    provincia_nombre: Optional[str] = Field(None, description="Nombre de provincia (para departamentos y localidades)")
    departamento_nombre: Optional[str] = Field(None, description="Nombre de departamento (para localidades)")


class EventoMapaResponse(BaseModel):
    """Respuesta del endpoint de mapa con eventos agrupados"""

    items: List[EventoMapaItem] = Field(default_factory=list)
    total: int = Field(..., description="Total de puntos en el mapa")
    nivel: Literal["provincia", "departamento", "localidad"] = Field(
        ..., description="Nivel de agregación aplicado"
    )


async def get_eventos_mapa(
    nivel: Literal["provincia", "departamento", "localidad"] = Query(
        "provincia",
        description="Nivel de agregación geográfica"
    ),
    id_provincia_indec: Optional[int] = Query(
        None,
        description="Filtrar por provincia (requerido para nivel departamento)"
    ),
    id_departamento_indec: Optional[int] = Query(
        None,
        description="Filtrar por departamento (requerido para nivel localidad)"
    ),
    id_grupo_eno: Optional[int] = Query(None, description="Filtrar por grupo ENO"),
    id_tipo_eno: Optional[int] = Query(None, description="Filtrar por tipo ENO"),
    session: Session = Depends(get_session),
) -> EventoMapaResponse:
    """
    Obtiene eventos agrupados por ubicación geográfica para visualización en mapa.

    Permite visualización jerárquica:
    - nivel=provincia: Muestra todas las provincias con conteo de eventos
    - nivel=departamento: Requiere id_provincia_indec, muestra departamentos de esa provincia
    - nivel=localidad: Requiere id_provincia_indec e id_departamento_indec, muestra localidades
    """

    items: List[EventoMapaItem] = []

    if nivel == "provincia":
        # Agrupar por provincia
        query = (
            select(
                Provincia.id_provincia_indec,
                Provincia.nombre,
                func.count(Evento.id).label("total_eventos"),
            )
            .select_from(Evento)
            .join(Domicilio, Evento.id_domicilio == Domicilio.id)
            .join(Localidad, Domicilio.id_localidad_indec == Localidad.id_localidad_indec)
            .join(Departamento, Localidad.id_departamento == Departamento.id)
            .join(Provincia, Departamento.id_provincia_indec == Provincia.id_provincia_indec)
        )

        # Aplicar filtros opcionales
        if id_grupo_eno is not None:
            query = query.where(
                Evento.id.in_(
                    select(EventoGrupoEno.id_evento).where(EventoGrupoEno.id_grupo_eno == id_grupo_eno)
                )
            )
        if id_tipo_eno is not None:
            query = query.where(Evento.id_tipo_eno == id_tipo_eno)

        query = query.group_by(Provincia.id_provincia_indec, Provincia.nombre)

        result = session.exec(query).all()

        for row in result:
            items.append(
                EventoMapaItem(
                    id=f"provincia_{row.id_provincia_indec}",
                    nombre=row.nombre,
                    nivel="provincia",
                    total_eventos=row.total_eventos,
                    id_provincia_indec=row.id_provincia_indec,
                    latitud=None,
                    longitud=None,
                )
            )

    elif nivel == "departamento":
        # Agrupar por departamento
        query = (
            select(
                Departamento.id_departamento_indec,
                Departamento.nombre,
                Provincia.id_provincia_indec,
                Provincia.nombre.label("provincia_nombre"),
                Departamento.latitud,
                Departamento.longitud,
                func.count(Evento.id).label("total_eventos"),
            )
            .select_from(Evento)
            .join(Domicilio, Evento.id_domicilio == Domicilio.id)
            .join(Localidad, Domicilio.id_localidad_indec == Localidad.id_localidad_indec)
            .join(Departamento, Localidad.id_departamento == Departamento.id)
            .join(Provincia, Departamento.id_provincia_indec == Provincia.id_provincia_indec)
        )

        # Aplicar filtros
        if id_provincia_indec is not None:
            query = query.where(Provincia.id_provincia_indec == id_provincia_indec)

        if id_grupo_eno is not None:
            query = query.where(
                Evento.id.in_(
                    select(EventoGrupoEno.id_evento).where(EventoGrupoEno.id_grupo_eno == id_grupo_eno)
                )
            )
        if id_tipo_eno is not None:
            query = query.where(Evento.id_tipo_eno == id_tipo_eno)

        query = query.group_by(
            Departamento.id_departamento_indec,
            Departamento.nombre,
            Provincia.id_provincia_indec,
            Provincia.nombre,
            Departamento.latitud,
            Departamento.longitud,
        )

        result = session.exec(query).all()

        for row in result:
            items.append(
                EventoMapaItem(
                    id=f"departamento_{row.id_provincia_indec}_{row.id_departamento_indec}",
                    nombre=row.nombre,
                    nivel="departamento",
                    total_eventos=row.total_eventos,
                    id_provincia_indec=row.id_provincia_indec,
                    id_departamento_indec=row.id_departamento_indec,
                    provincia_nombre=row.provincia_nombre,
                    latitud=float(row.latitud) if row.latitud else None,
                    longitud=float(row.longitud) if row.longitud else None,
                )
            )

    elif nivel == "localidad":
        # Agrupar por localidad
        query = (
            select(
                Localidad.id_localidad_indec,
                Localidad.nombre,
                Departamento.id_departamento_indec,
                Departamento.nombre.label("departamento_nombre"),
                Provincia.id_provincia_indec,
                Provincia.nombre.label("provincia_nombre"),
                Localidad.latitud,
                Localidad.longitud,
                func.count(Evento.id).label("total_eventos"),
            )
            .select_from(Evento)
            .join(Domicilio, Evento.id_domicilio == Domicilio.id)
            .join(Localidad, Domicilio.id_localidad_indec == Localidad.id_localidad_indec)
            .join(Departamento, Localidad.id_departamento == Departamento.id)
            .join(Provincia, Departamento.id_provincia_indec == Provincia.id_provincia_indec)
        )

        # Aplicar filtros
        if id_provincia_indec is not None:
            query = query.where(Provincia.id_provincia_indec == id_provincia_indec)
        if id_departamento_indec is not None:
            query = query.where(Departamento.id_departamento_indec == id_departamento_indec)

        if id_grupo_eno is not None:
            query = query.where(
                Evento.id.in_(
                    select(EventoGrupoEno.id_evento).where(EventoGrupoEno.id_grupo_eno == id_grupo_eno)
                )
            )
        if id_tipo_eno is not None:
            query = query.where(Evento.id_tipo_eno == id_tipo_eno)

        query = query.group_by(
            Localidad.id_localidad_indec,
            Localidad.nombre,
            Departamento.id_departamento_indec,
            Departamento.nombre,
            Provincia.id_provincia_indec,
            Provincia.nombre,
            Localidad.latitud,
            Localidad.longitud,
        )

        result = session.exec(query).all()

        for row in result:
            items.append(
                EventoMapaItem(
                    id=f"localidad_{row.id_localidad_indec}",
                    nombre=row.nombre,
                    nivel="localidad",
                    total_eventos=row.total_eventos,
                    id_provincia_indec=row.id_provincia_indec,
                    id_departamento_indec=row.id_departamento_indec,
                    id_localidad_indec=row.id_localidad_indec,
                    provincia_nombre=row.provincia_nombre,
                    departamento_nombre=row.departamento_nombre,
                    latitud=float(row.latitud) if row.latitud else None,
                    longitud=float(row.longitud) if row.longitud else None,
                )
            )

    response = EventoMapaResponse(
        items=items,
        total=len(items),
        nivel=nivel,
    )

    return SuccessResponse(data=response)
