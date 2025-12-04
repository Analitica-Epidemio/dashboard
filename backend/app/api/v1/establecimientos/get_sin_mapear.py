"""Endpoint para obtener establecimientos sin mapear con sugerencias."""

from fastapi import Depends, Query
from sqlalchemy import func, or_, select
from sqlmodel import Session

from app.core.database import get_session
from app.domains.eventos_epidemiologicos.eventos.models import Evento
from app.domains.territorio.establecimientos_models import Establecimiento
from app.domains.territorio.geografia_models import Departamento, Localidad, Provincia

from .mapeo_schemas import EstablecimientoSinMapear, EstablecimientosSinMapearResponse
from .suggestions_service import buscar_sugerencias_para_establecimiento


async def get_establecimientos_sin_mapear(
    limit: int = Query(50, ge=1, le=200, description="Número de resultados por página"),
    offset: int = Query(0, ge=0, description="Número de resultados a saltar"),
    con_eventos_solo: bool = Query(True, description="Solo mostrar establecimientos con eventos"),
    incluir_sugerencias: bool = Query(True, description="Incluir sugerencias automáticas"),
    session: Session = Depends(get_session),
) -> EstablecimientosSinMapearResponse:
    """
    Obtiene establecimientos SNVS sin mapear a IGN, con sugerencias automáticas.

    Los establecimientos sin mapear son aquellos con source='SNVS' y sin codigo_refes.
    Se priorizan por cantidad de eventos descendente.
    """
    # Query base: establecimientos SNVS sin REFES
    base_query = (
        select(
            Establecimiento.id,
            Establecimiento.nombre,
            Establecimiento.codigo_snvs,
            Localidad.nombre.label("localidad_nombre"),
            Departamento.nombre.label("departamento_nombre"),
            Provincia.nombre.label("provincia_nombre"),
            func.count(Evento.id).label("total_eventos")
        )
        .outerjoin(Localidad, Establecimiento.id_localidad_indec == Localidad.id_localidad_indec)
        .outerjoin(Departamento, Localidad.id_departamento_indec == Departamento.id_departamento_indec)
        .outerjoin(Provincia, Departamento.id_provincia_indec == Provincia.id_provincia_indec)
        .outerjoin(
            Evento,
            or_(
                Evento.id_establecimiento_carga == Establecimiento.id,
                Evento.id_establecimiento_consulta == Establecimiento.id,
                Evento.id_establecimiento_notificacion == Establecimiento.id
            )
        )
        .where(Establecimiento.source == "SNVS")
        .where(Establecimiento.codigo_refes.is_(None))  # Sin mapear
        .group_by(
            Establecimiento.id,
            Establecimiento.nombre,
            Establecimiento.codigo_snvs,
            Localidad.nombre,
            Departamento.nombre,
            Provincia.nombre
        )
    )

    if con_eventos_solo:
        base_query = base_query.having(func.count(Evento.id) > 0)

    # Ordenar por número de eventos descendente (más impacto primero)
    base_query = base_query.order_by(func.count(Evento.id).desc())

    # Contar total
    count_query = select(func.count()).select_from(base_query.subquery())
    total = session.exec(count_query).one()

    # Obtener resultados paginados
    results_query = base_query.offset(offset).limit(limit)
    results = session.exec(results_query).all()

    # Construir respuesta con sugerencias
    items = []
    for row in results:
        estab = EstablecimientoSinMapear(
            id=row[0],
            nombre=row[1],
            codigo_snvs=row[2],
            localidad_nombre=row[3],
            departamento_nombre=row[4],
            provincia_nombre=row[5],
            total_eventos=row[6],
            sugerencias=[]
        )

        # Buscar sugerencias si está habilitado
        if incluir_sugerencias:
            sugerencias = await buscar_sugerencias_para_establecimiento(
                session=session,
                nombre_snvs=row[1],
                provincia_nombre_snvs=row[5],
                departamento_nombre_snvs=row[4],
                localidad_nombre_snvs=row[3],
                limit=3  # Top 3 sugerencias por establecimiento
            )
            estab.sugerencias = sugerencias

        items.append(estab)

    # Contar estadísticas generales
    stats_query = select(
        func.count(Establecimiento.id).label("sin_mapear_count"),
        func.coalesce(func.sum(
            func.count(Evento.id)
        ), 0).label("eventos_sin_mapear_count")
    ).select_from(Establecimiento).outerjoin(
        Evento,
        or_(
            Evento.id_establecimiento_carga == Establecimiento.id,
            Evento.id_establecimiento_consulta == Establecimiento.id,
            Evento.id_establecimiento_notificacion == Establecimiento.id
        )
    ).where(
        Establecimiento.source == "SNVS",
        Establecimiento.codigo_refes.is_(None)
    ).group_by(Establecimiento.id)

    stats = session.exec(stats_query).first()
    sin_mapear_count = stats[0] if stats else 0
    eventos_sin_mapear_count = stats[1] if stats else 0

    return EstablecimientosSinMapearResponse(
        items=items,
        total=total,
        sin_mapear_count=sin_mapear_count,
        eventos_sin_mapear_count=eventos_sin_mapear_count
    )
