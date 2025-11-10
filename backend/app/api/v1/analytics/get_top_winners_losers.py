"""
Get top winners/losers endpoint - entidades con mayor cambio
"""

import logging
from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.analytics.period_utils import (
    create_period_info,
    get_comparison_period,
    get_period_dates,
    get_period_description,
)
from app.api.v1.analytics.schemas import (
    PeriodType,
    TopWinnerLoser,
    TopWinnersLosersResponse,
)
from app.core.database import get_async_session
from app.core.schemas.response import SuccessResponse
from app.core.security import RequireAuthOrSignedUrl
from app.domains.autenticacion.models import User

logger = logging.getLogger(__name__)


async def get_top_winners_losers(
    metric_type: str = Query("departamentos", description="Tipo de métrica: departamentos, tipo_eno, provincias"),
    period_type: PeriodType = Query(PeriodType.ULTIMAS_4_SEMANAS_EPI, description="Tipo de período predefinido"),
    fecha_desde: Optional[date] = Query(None, description="Fecha desde (solo si period_type=personalizado)"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha hasta (solo si period_type=personalizado)"),
    fecha_referencia: Optional[date] = Query(None, description="Fecha de referencia para 'viajar en el tiempo' (ej: 2023-03-15)"),
    grupo_id: Optional[int] = Query(None, description="ID del grupo seleccionado"),
    tipo_eno_ids: Optional[List[int]] = Query(None, description="IDs de los eventos a filtrar"),
    clasificaciones: Optional[List[str]] = Query(None, description="Filtrar por clasificaciones estratégicas"),
    provincia_id: Optional[int] = Query(None, description="Código INDEC de provincia (solo para metric_type=departamentos)"),
    limit: int = Query(10, description="Número de winners/losers a retornar"),
    db: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = RequireAuthOrSignedUrl
) -> SuccessResponse[TopWinnersLosersResponse]:
    """
    Endpoint para obtener top winners y losers.

    Winners: Entidades con mayor aumento en casos
    Losers: Entidades con mayor disminución en casos
    """

    # Determinar fechas del período actual
    if period_type == PeriodType.PERSONALIZADO:
        if not fecha_desde or not fecha_hasta:
            raise ValueError("Para período personalizado debe especificar fecha_desde y fecha_hasta")
        periodo_desde = fecha_desde
        periodo_hasta = fecha_hasta
    else:
        periodo_desde, periodo_hasta = get_period_dates(
            period_type,
            fecha_referencia=fecha_referencia
        )

    # Período de comparación (siempre rolling para winners/losers)
    comp_desde, comp_hasta = get_comparison_period(periodo_desde, periodo_hasta, "rolling")

    # Crear PeriodInfo
    descripcion_actual = get_period_description(period_type, periodo_desde, periodo_hasta)
    periodo_actual = create_period_info(periodo_desde, periodo_hasta, descripcion_actual)
    descripcion_comp = f"Período anterior ({comp_desde.strftime('%d/%m')} - {comp_hasta.strftime('%d/%m')})"
    periodo_comparacion = create_period_info(comp_desde, comp_hasta, descripcion_comp)

    # Construir WHERE clauses
    params: Dict[str, Any] = {}
    where_clauses_base = []

    if provincia_id and metric_type == "departamentos":
        where_clauses_base.append("d.id_provincia_indec = :provincia_id")
        params["provincia_id"] = provincia_id

    if grupo_id:
        where_clauses_base.append("""
            e.id_tipo_eno IN (
                SELECT id_tipo_eno FROM tipo_eno_grupo_eno WHERE id_grupo_eno = :grupo_id
            )
        """)
        params["grupo_id"] = grupo_id

    if tipo_eno_ids and len(tipo_eno_ids) > 0:
        where_clauses_base.append("e.id_tipo_eno = ANY(:tipo_eno_ids)")
        params["tipo_eno_ids"] = tipo_eno_ids

    if clasificaciones:
        where_clauses_base.append("e.clasificacion_estrategia = ANY(:clasificaciones)")
        params["clasificaciones"] = clasificaciones

    where_sql_base = " AND ".join(where_clauses_base) if where_clauses_base else "1=1"

    # Construir base query según metric_type (CTE compartido)
    if metric_type == "departamentos":
        base_cte = f"""
        WITH casos_actual AS (
            SELECT
                d.id_departamento_indec as entidad_id,
                d.nombre as entidad_nombre,
                COUNT(DISTINCT e.id) as casos
            FROM evento e
            LEFT JOIN establecimiento est ON e.id_establecimiento_notificacion = est.id
            LEFT JOIN localidad l ON est.id_localidad_indec = l.id_localidad_indec
            LEFT JOIN departamento d ON l.id_departamento_indec = d.id_departamento_indec
            WHERE e.fecha_minima_evento >= :fecha_desde_actual
                AND e.fecha_minima_evento <= :fecha_hasta_actual
                AND d.id_departamento_indec IS NOT NULL
                AND {where_sql_base}
            GROUP BY d.id_departamento_indec, d.nombre
        ),
        casos_anterior AS (
            SELECT
                d.id_departamento_indec as entidad_id,
                COUNT(DISTINCT e.id) as casos
            FROM evento e
            LEFT JOIN establecimiento est ON e.id_establecimiento_notificacion = est.id
            LEFT JOIN localidad l ON est.id_localidad_indec = l.id_localidad_indec
            LEFT JOIN departamento d ON l.id_departamento_indec = d.id_departamento_indec
            WHERE e.fecha_minima_evento >= :fecha_desde_comp
                AND e.fecha_minima_evento <= :fecha_hasta_comp
                AND d.id_departamento_indec IS NOT NULL
                AND {where_sql_base}
            GROUP BY d.id_departamento_indec
        ),
        cambios AS (
            SELECT
                a.entidad_id,
                a.entidad_nombre,
                a.casos as valor_actual,
                COALESCE(b.casos, 0) as valor_anterior,
                (a.casos - COALESCE(b.casos, 0)) as diferencia_absoluta,
                CASE
                    WHEN COALESCE(b.casos, 0) = 0 THEN NULL
                    ELSE ((a.casos - COALESCE(b.casos, 0))::float / b.casos * 100)
                END as diferencia_porcentual
            FROM casos_actual a
            LEFT JOIN casos_anterior b ON a.entidad_id = b.entidad_id
            WHERE COALESCE(b.casos, 0) > 0
        )
        """

    elif metric_type == "tipo_eno":
        base_cte = f"""
        WITH casos_actual AS (
            SELECT
                te.id as entidad_id,
                te.nombre as entidad_nombre,
                COUNT(DISTINCT e.id) as casos
            FROM evento e
            INNER JOIN tipo_eno te ON e.id_tipo_eno = te.id
            LEFT JOIN establecimiento est ON e.id_establecimiento_notificacion = est.id
            LEFT JOIN localidad l ON est.id_localidad_indec = l.id_localidad_indec
            LEFT JOIN departamento d ON l.id_departamento_indec = d.id_departamento_indec
            WHERE e.fecha_minima_evento >= :fecha_desde_actual
                AND e.fecha_minima_evento <= :fecha_hasta_actual
                AND {where_sql_base}
            GROUP BY te.id, te.nombre
        ),
        casos_anterior AS (
            SELECT
                te.id as entidad_id,
                COUNT(DISTINCT e.id) as casos
            FROM evento e
            INNER JOIN tipo_eno te ON e.id_tipo_eno = te.id
            LEFT JOIN establecimiento est ON e.id_establecimiento_notificacion = est.id
            LEFT JOIN localidad l ON est.id_localidad_indec = l.id_localidad_indec
            LEFT JOIN departamento d ON l.id_departamento_indec = d.id_departamento_indec
            WHERE e.fecha_minima_evento >= :fecha_desde_comp
                AND e.fecha_minima_evento <= :fecha_hasta_comp
                AND {where_sql_base}
            GROUP BY te.id
        ),
        cambios AS (
            SELECT
                a.entidad_id,
                a.entidad_nombre,
                a.casos as valor_actual,
                COALESCE(b.casos, 0) as valor_anterior,
                (a.casos - COALESCE(b.casos, 0)) as diferencia_absoluta,
                CASE
                    WHEN COALESCE(b.casos, 0) = 0 THEN NULL
                    ELSE ((a.casos - COALESCE(b.casos, 0))::float / b.casos * 100)
                END as diferencia_porcentual
            FROM casos_actual a
            LEFT JOIN casos_anterior b ON a.entidad_id = b.entidad_id
            WHERE COALESCE(b.casos, 0) > 0
        )
        """

    elif metric_type == "provincias":
        base_cte = f"""
        WITH casos_actual AS (
            SELECT
                p.id_provincia_indec as entidad_id,
                p.nombre as entidad_nombre,
                COUNT(DISTINCT e.id) as casos
            FROM evento e
            LEFT JOIN establecimiento est ON e.id_establecimiento_notificacion = est.id
            LEFT JOIN localidad l ON est.id_localidad_indec = l.id_localidad_indec
            LEFT JOIN departamento d ON l.id_departamento_indec = d.id_departamento_indec
            LEFT JOIN provincia p ON d.id_provincia_indec = p.id_provincia_indec
            WHERE e.fecha_minima_evento >= :fecha_desde_actual
                AND e.fecha_minima_evento <= :fecha_hasta_actual
                AND p.id_provincia_indec IS NOT NULL
                AND {where_sql_base}
            GROUP BY p.id_provincia_indec, p.nombre
        ),
        casos_anterior AS (
            SELECT
                p.id_provincia_indec as entidad_id,
                COUNT(DISTINCT e.id) as casos
            FROM evento e
            LEFT JOIN establecimiento est ON e.id_establecimiento_notificacion = est.id
            LEFT JOIN localidad l ON est.id_localidad_indec = l.id_localidad_indec
            LEFT JOIN departamento d ON l.id_departamento_indec = d.id_departamento_indec
            LEFT JOIN provincia p ON d.id_provincia_indec = p.id_provincia_indec
            WHERE e.fecha_minima_evento >= :fecha_desde_comp
                AND e.fecha_minima_evento <= :fecha_hasta_comp
                AND p.id_provincia_indec IS NOT NULL
                AND {where_sql_base}
            GROUP BY p.id_provincia_indec
        ),
        cambios AS (
            SELECT
                a.entidad_id,
                a.entidad_nombre,
                a.casos as valor_actual,
                COALESCE(b.casos, 0) as valor_anterior,
                (a.casos - COALESCE(b.casos, 0)) as diferencia_absoluta,
                CASE
                    WHEN COALESCE(b.casos, 0) = 0 THEN NULL
                    ELSE ((a.casos - COALESCE(b.casos, 0))::float / b.casos * 100)
                END as diferencia_porcentual
            FROM casos_actual a
            LEFT JOIN casos_anterior b ON a.entidad_id = b.entidad_id
            WHERE COALESCE(b.casos, 0) > 0
        )
        """
    else:
        raise ValueError(f"metric_type inválido: {metric_type}")

    # Query para winners (aumentos > 0)
    query_winners = base_cte + """
        SELECT
            entidad_id,
            entidad_nombre,
            valor_actual,
            valor_anterior,
            diferencia_absoluta,
            diferencia_porcentual
        FROM cambios
        WHERE diferencia_porcentual > 0
        ORDER BY diferencia_porcentual DESC
        LIMIT :limit
    """

    # Query para losers (disminuciones < 0)
    query_losers = base_cte + """
        SELECT
            entidad_id,
            entidad_nombre,
            valor_actual,
            valor_anterior,
            diferencia_absoluta,
            diferencia_porcentual
        FROM cambios
        WHERE diferencia_porcentual < 0
        ORDER BY diferencia_porcentual ASC
        LIMIT :limit
    """

    # Preparar parámetros
    params.update({
        "fecha_desde_actual": periodo_desde,
        "fecha_hasta_actual": periodo_hasta,
        "fecha_desde_comp": comp_desde,
        "fecha_hasta_comp": comp_hasta,
        "limit": limit
    })

    # Ejecutar query para winners
    result_winners = await db.execute(text(query_winners), params)
    rows_winners = result_winners.fetchall()

    # Ejecutar query para losers
    result_losers = await db.execute(text(query_losers), params)
    rows_losers = result_losers.fetchall()

    # Procesar winners
    winners = []
    for row in rows_winners:
        if row.diferencia_porcentual is not None:
            winners.append(TopWinnerLoser(
                entidad_id=row.entidad_id,
                entidad_nombre=row.entidad_nombre,
                valor_actual=float(row.valor_actual),
                valor_anterior=float(row.valor_anterior),
                diferencia_porcentual=round(float(row.diferencia_porcentual), 2),
                diferencia_absoluta=float(row.diferencia_absoluta)
            ))

    # Procesar losers
    losers = []
    for row in rows_losers:
        if row.diferencia_porcentual is not None:
            losers.append(TopWinnerLoser(
                entidad_id=row.entidad_id,
                entidad_nombre=row.entidad_nombre,
                valor_actual=float(row.valor_actual),
                valor_anterior=float(row.valor_anterior),
                diferencia_porcentual=round(float(row.diferencia_porcentual), 2),
                diferencia_absoluta=float(row.diferencia_absoluta)
            ))

    response = TopWinnersLosersResponse(
        top_winners=winners,
        top_losers=losers,
        metric_type=metric_type,
        periodo_actual=periodo_actual,
        periodo_comparacion=periodo_comparacion
    )

    return SuccessResponse(data=response)
