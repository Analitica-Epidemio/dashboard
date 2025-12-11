"""Endpoint para listar mapeos existentes."""

from typing import Optional

from fastapi import Depends, Query
from sqlalchemy import func, or_, select
from sqlmodel import Session, col

from app.core.database import get_session
from app.domains.territorio.establecimientos_models import Establecimiento
from app.domains.territorio.geografia_models import Departamento, Localidad, Provincia
from app.domains.vigilancia_nominal.models.caso import CasoEpidemiologico

from .mapeo_schemas import MapeoInfo, MapeosListResponse


async def listar_mapeos_existentes(
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(50, ge=1, le=200, description="Resultados por página"),
    confianza: Optional[str] = Query(
        None, description="Filtrar por confianza: HIGH, MEDIUM, LOW"
    ),
    validados_solo: bool = Query(False, description="Solo mostrar mapeos validados"),
    manuales_solo: bool = Query(False, description="Solo mostrar mapeos manuales"),
    session: Session = Depends(get_session),
) -> MapeosListResponse:
    """
    Lista mapeos existentes SNVS → IGN con metadata.

    Muestra establecimientos SNVS que tienen codigo_refes asignado.
    """
    offset = (page - 1) * page_size

    # Subquery para contar eventos por establecimiento SNVS
    eventos_subquery = (
        select(
            col(Establecimiento.id).label("estab_id"),
            func.count(CasoEpidemiologico.id).label("total_eventos"),
        )
        .outerjoin(
            CasoEpidemiologico,
            or_(
                col(CasoEpidemiologico.id_establecimiento_carga)
                == col(Establecimiento.id),
                col(CasoEpidemiologico.id_establecimiento_consulta)
                == col(Establecimiento.id),
                col(CasoEpidemiologico.id_establecimiento_notificacion)
                == col(Establecimiento.id),
            ),
        )
        .group_by(Establecimiento.id)
        .subquery()
    )

    # Query principal
    query = (
        select(
            col(Establecimiento.id).label("id_snvs"),
            col(Establecimiento.nombre).label("nombre_snvs"),
            col(Establecimiento.codigo_snvs),
            col(Establecimiento.mapeo_score),
            col(Establecimiento.mapeo_similitud_nombre),
            col(Establecimiento.mapeo_confianza),
            col(Establecimiento.mapeo_razon),
            col(Establecimiento.mapeo_es_manual),
            col(Establecimiento.mapeo_validado),
            col(Establecimiento.codigo_refes),
            func.coalesce(eventos_subquery.c.total_eventos, 0).label("total_eventos"),
            col(Localidad.nombre).label("localidad_nombre_snvs"),
            col(Provincia.nombre).label("provincia_nombre_snvs"),
        )
        .outerjoin(eventos_subquery, eventos_subquery.c.estab_id == Establecimiento.id)
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
        .where(col(Establecimiento.source) == "SNVS")
        .where(col(Establecimiento.codigo_refes).is_not(None))
    )

    # Aplicar filtros
    if confianza:
        query = query.where(col(Establecimiento.mapeo_confianza) == confianza.upper())

    if validados_solo:
        query = query.where(col(Establecimiento.mapeo_validado).is_(True))

    if manuales_solo:
        query = query.where(col(Establecimiento.mapeo_es_manual).is_(True))

    # Ordenar por score descendente
    query = query.order_by(col(Establecimiento.mapeo_score).desc())

    # Contar total
    count_query = select(func.count()).select_from(query.subquery())
    total = session.exec(count_query).one()[0]

    # Obtener resultados paginados
    results_query = query.offset(offset).limit(page_size)
    results = session.execute(results_query).all()

    # Construir respuesta
    # Para cada establecimiento SNVS mapeado, buscar el establecimiento IGN correspondiente
    items = []
    for row in results:
        codigo_refes = row[9]

        # Buscar establecimiento IGN con ese codigo_refes
        estab_ign = session.exec(
            select(Establecimiento, col(Localidad.nombre), col(Provincia.nombre))
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
            .where(col(Establecimiento.source) == "IGN")
            .where(col(Establecimiento.codigo_refes) == codigo_refes)
        ).first()

        if estab_ign:
            ign_data = estab_ign[0]
            localidad_ign = estab_ign[1]
            provincia_ign = estab_ign[2]
        else:
            # No debería pasar, pero por seguridad
            ign_data = None
            localidad_ign = None
            provincia_ign = None

        items.append(
            MapeoInfo(
                id_establecimiento_snvs=row[0],
                nombre_snvs=row[1],
                codigo_snvs=row[2],
                id_establecimiento_ign=ign_data.id if ign_data else None,
                nombre_ign=ign_data.nombre if ign_data else "Desconocido",
                codigo_refes=codigo_refes,
                mapeo_score=row[3],
                mapeo_similitud_nombre=row[4],
                mapeo_confianza=row[5],
                mapeo_razon=row[6],
                mapeo_es_manual=row[7],
                mapeo_validado=row[8],
                total_eventos=row[10],
                localidad_nombre_snvs=row[11],
                localidad_nombre_ign=localidad_ign,
                provincia_nombre_snvs=row[12],
                provincia_nombre_ign=provincia_ign,
            )
        )

    return MapeosListResponse(items=items, total=total, page=page, page_size=page_size)
