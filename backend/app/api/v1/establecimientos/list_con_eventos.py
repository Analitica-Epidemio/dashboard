"""
Endpoint para listar establecimientos con conteo de eventos relacionados.
Similar al listado de domicilios.
"""

from typing import List, Optional

from fastapi import Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, or_
from sqlmodel import Session

from app.core.database import get_session
from app.core.schemas.response import SuccessResponse
from app.domains.territorio.establecimientos_models import Establecimiento
from app.domains.territorio.geografia_models import Localidad, Departamento, Provincia
from app.domains.eventos_epidemiologicos.eventos.models import Evento
from app.domains.atencion_medica.salud_models import MuestraEvento
from app.domains.atencion_medica.diagnosticos_models import DiagnosticoEvento, TratamientoEvento


class EstablecimientoListItem(BaseModel):
    """Item de establecimiento en el listado"""

    id: int = Field(..., description="ID del establecimiento")
    nombre: str = Field(..., description="Nombre del establecimiento")
    codigo_refes: Optional[str] = Field(None, description="Código REFES")
    codigo_snvs: Optional[str] = Field(None, description="Código SNVS")
    source: Optional[str] = Field(None, description="Fuente del dato (IGN, SNVS)")

    # Ubicación
    localidad_nombre: Optional[str] = Field(None, description="Nombre de la localidad")
    departamento_nombre: Optional[str] = Field(None, description="Nombre del departamento")
    provincia_nombre: Optional[str] = Field(None, description="Nombre de la provincia")

    # Coordenadas
    latitud: Optional[float] = Field(None, description="Latitud")
    longitud: Optional[float] = Field(None, description="Longitud")

    # Conteo de eventos
    total_eventos: int = Field(0, description="Total de eventos relacionados")
    eventos_consulta: int = Field(0, description="Eventos donde fue consulta")
    eventos_notificacion: int = Field(0, description="Eventos donde fue notificación")
    eventos_carga: int = Field(0, description="Eventos donde fue carga")
    eventos_muestra: int = Field(0, description="Eventos con muestras")
    eventos_diagnostico: int = Field(0, description="Eventos con diagnósticos")
    eventos_tratamiento: int = Field(0, description="Eventos con tratamientos")


class EstablecimientosListResponse(BaseModel):
    """Respuesta con lista paginada de establecimientos"""

    items: List[EstablecimientoListItem] = Field(default_factory=list)
    total: int = Field(..., description="Total de establecimientos")
    page: int = Field(..., description="Página actual")
    page_size: int = Field(..., description="Tamaño de página")
    total_pages: int = Field(..., description="Total de páginas")


async def list_establecimientos_con_eventos(
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(50, ge=1, le=200, description="Tamaño de página"),
    order_by: str = Query(
        "eventos_desc",
        description="Ordenar por: eventos_desc, eventos_asc, nombre_asc, source_asc",
    ),
    source: Optional[str] = Query(None, description="Filtrar por fuente (IGN, SNVS)"),
    tiene_eventos: Optional[bool] = Query(
        None, description="Filtrar solo con eventos (true) o sin eventos (false)"
    ),
    session: Session = Depends(get_session),
) -> SuccessResponse[EstablecimientosListResponse]:
    """
    Lista establecimientos con conteo de eventos relacionados.

    Cuenta eventos de todas las tablas relacionadas:
    - Evento (consulta, notificación, carga)
    - MuestraEvento
    - DiagnosticoEvento
    - TratamientoEvento
    """

    # Subquery para contar eventos de cada tipo
    eventos_consulta_sq = (
        select(
            Evento.id_establecimiento_consulta.label("id_estab"),
            func.count(Evento.id).label("count"),
        )
        .where(Evento.id_establecimiento_consulta.isnot(None))
        .group_by(Evento.id_establecimiento_consulta)
        .subquery()
    )

    eventos_notif_sq = (
        select(
            Evento.id_establecimiento_notificacion.label("id_estab"),
            func.count(Evento.id).label("count"),
        )
        .where(Evento.id_establecimiento_notificacion.isnot(None))
        .group_by(Evento.id_establecimiento_notificacion)
        .subquery()
    )

    eventos_carga_sq = (
        select(
            Evento.id_establecimiento_carga.label("id_estab"),
            func.count(Evento.id).label("count"),
        )
        .where(Evento.id_establecimiento_carga.isnot(None))
        .group_by(Evento.id_establecimiento_carga)
        .subquery()
    )

    muestras_sq = (
        select(
            MuestraEvento.id_establecimiento.label("id_estab"),
            func.count(MuestraEvento.id).label("count"),
        )
        .where(MuestraEvento.id_establecimiento.isnot(None))
        .group_by(MuestraEvento.id_establecimiento)
        .subquery()
    )

    diagnosticos_sq = (
        select(
            DiagnosticoEvento.id_establecimiento_diagnostico.label("id_estab"),
            func.count(DiagnosticoEvento.id).label("count"),
        )
        .where(DiagnosticoEvento.id_establecimiento_diagnostico.isnot(None))
        .group_by(DiagnosticoEvento.id_establecimiento_diagnostico)
        .subquery()
    )

    tratamientos_sq = (
        select(
            TratamientoEvento.id_establecimiento_tratamiento.label("id_estab"),
            func.count(TratamientoEvento.id).label("count"),
        )
        .where(TratamientoEvento.id_establecimiento_tratamiento.isnot(None))
        .group_by(TratamientoEvento.id_establecimiento_tratamiento)
        .subquery()
    )

    # Query principal
    query = (
        select(
            Establecimiento,
            Localidad.nombre.label("localidad_nombre"),
            Departamento.nombre.label("departamento_nombre"),
            Provincia.nombre.label("provincia_nombre"),
            func.coalesce(eventos_consulta_sq.c.count, 0).label("eventos_consulta"),
            func.coalesce(eventos_notif_sq.c.count, 0).label("eventos_notificacion"),
            func.coalesce(eventos_carga_sq.c.count, 0).label("eventos_carga"),
            func.coalesce(muestras_sq.c.count, 0).label("eventos_muestra"),
            func.coalesce(diagnosticos_sq.c.count, 0).label("eventos_diagnostico"),
            func.coalesce(tratamientos_sq.c.count, 0).label("eventos_tratamiento"),
            (
                func.coalesce(eventos_consulta_sq.c.count, 0)
                + func.coalesce(eventos_notif_sq.c.count, 0)
                + func.coalesce(eventos_carga_sq.c.count, 0)
                + func.coalesce(muestras_sq.c.count, 0)
                + func.coalesce(diagnosticos_sq.c.count, 0)
                + func.coalesce(tratamientos_sq.c.count, 0)
            ).label("total_eventos"),
        )
        .outerjoin(
            Localidad, Establecimiento.id_localidad_indec == Localidad.id_localidad_indec
        )
        .outerjoin(
            Departamento,
            Localidad.id_departamento_indec == Departamento.id_departamento_indec,
        )
        .outerjoin(
            Provincia, Departamento.id_provincia_indec == Provincia.id_provincia_indec
        )
        .outerjoin(eventos_consulta_sq, Establecimiento.id == eventos_consulta_sq.c.id_estab)
        .outerjoin(eventos_notif_sq, Establecimiento.id == eventos_notif_sq.c.id_estab)
        .outerjoin(eventos_carga_sq, Establecimiento.id == eventos_carga_sq.c.id_estab)
        .outerjoin(muestras_sq, Establecimiento.id == muestras_sq.c.id_estab)
        .outerjoin(diagnosticos_sq, Establecimiento.id == diagnosticos_sq.c.id_estab)
        .outerjoin(tratamientos_sq, Establecimiento.id == tratamientos_sq.c.id_estab)
    )

    # Aplicar filtros
    if source:
        query = query.where(Establecimiento.source == source)

    if tiene_eventos is not None:
        total_eventos_expr = (
            func.coalesce(eventos_consulta_sq.c.count, 0)
            + func.coalesce(eventos_notif_sq.c.count, 0)
            + func.coalesce(eventos_carga_sq.c.count, 0)
            + func.coalesce(muestras_sq.c.count, 0)
            + func.coalesce(diagnosticos_sq.c.count, 0)
            + func.coalesce(tratamientos_sq.c.count, 0)
        )
        if tiene_eventos:
            query = query.where(total_eventos_expr > 0)
        else:
            query = query.where(total_eventos_expr == 0)

    # Contar total antes de paginar
    count_query = select(func.count()).select_from(query.subquery())
    total_result = session.exec(count_query).one()
    total = int(total_result[0]) if total_result else 0

    # Ordenar
    if order_by == "eventos_desc":
        query = query.order_by(
            (
                func.coalesce(eventos_consulta_sq.c.count, 0)
                + func.coalesce(eventos_notif_sq.c.count, 0)
                + func.coalesce(eventos_carga_sq.c.count, 0)
                + func.coalesce(muestras_sq.c.count, 0)
                + func.coalesce(diagnosticos_sq.c.count, 0)
                + func.coalesce(tratamientos_sq.c.count, 0)
            ).desc()
        )
    elif order_by == "eventos_asc":
        query = query.order_by(
            (
                func.coalesce(eventos_consulta_sq.c.count, 0)
                + func.coalesce(eventos_notif_sq.c.count, 0)
                + func.coalesce(eventos_carga_sq.c.count, 0)
                + func.coalesce(muestras_sq.c.count, 0)
                + func.coalesce(diagnosticos_sq.c.count, 0)
                + func.coalesce(tratamientos_sq.c.count, 0)
            ).asc()
        )
    elif order_by == "nombre_asc":
        query = query.order_by(Establecimiento.nombre.asc())
    elif order_by == "source_asc":
        query = query.order_by(Establecimiento.source.asc())

    # Paginar
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Ejecutar query
    results = session.exec(query).all()

    # Construir items
    items = []
    for row in results:
        estab = row[0]
        item = EstablecimientoListItem(
            id=estab.id,
            nombre=estab.nombre,
            codigo_refes=estab.codigo_refes,
            codigo_snvs=estab.codigo_snvs,
            source=estab.source,
            localidad_nombre=row.localidad_nombre,
            departamento_nombre=row.departamento_nombre,
            provincia_nombre=row.provincia_nombre,
            latitud=float(estab.latitud) if estab.latitud else None,
            longitud=float(estab.longitud) if estab.longitud else None,
            total_eventos=row.total_eventos,
            eventos_consulta=row.eventos_consulta,
            eventos_notificacion=row.eventos_notificacion,
            eventos_carga=row.eventos_carga,
            eventos_muestra=row.eventos_muestra,
            eventos_diagnostico=row.eventos_diagnostico,
            eventos_tratamiento=row.eventos_tratamiento,
        )
        items.append(item)

    # Calcular total de páginas
    total_pages = (total + page_size - 1) // page_size

    response_data = EstablecimientosListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )

    return SuccessResponse(data=response_data)
